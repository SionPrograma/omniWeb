import os
import shutil
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ChipEditor:
    """
    Applies patches to chip files with safety checks and backups.
    """
    def apply_patches(self, chip_slug: str, patches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Applies a list of patches to a chip with safety rollbacks.
        """
        folder_name = f"chip-{chip_slug}" if not chip_slug.startswith("chip-") else chip_slug
        chip_path = os.path.join("chips", folder_name)
        
        if not os.path.exists(chip_path):
             return {"status": "error", "message": f"Chip {folder_name} not found."}

        backup_dir = os.path.join("backend", "data", "backups", "ai_developer")
        os.makedirs(backup_dir, exist_ok=True)
        import time
        backup_path = os.path.join(backup_dir, f"{folder_name}_pre_patch_{int(time.time())}")
        
        # 1. Create backup
        try:
             shutil.copytree(chip_path, backup_path, dirs_exist_ok=True)
             logger.info(f"Created backup at {backup_path}")
        except Exception as e:
             return {"status": "error", "message": f"Backup failed: {e}"}
             
        applied = []
        try:
            for patch in patches:
                file_rel_path = patch["file"]
                file_abs_path = os.path.join(chip_path, file_rel_path)
                
                if not os.path.exists(file_abs_path):
                    logger.warning(f"File {file_rel_path} not found in {folder_name}")
                    continue
                    
                with open(file_abs_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                new_content = content
                action = patch.get("action")
                
                if action == "insert_before":
                    target = patch.get("target")
                    if target in content:
                        new_content = content.replace(target, f"{patch['content']}\n{target}")
                elif action == "append":
                    new_content = content + f"\n{patch['content']}"
                elif action == "replace":
                    target = patch.get("target")
                    if target in content:
                        new_content = content.replace(target, patch["content"])
                
                # Internal Syntax check for .py files
                if file_rel_path.endswith(".py"):
                    try:
                        compile(new_content, file_rel_path, 'exec')
                    except SyntaxError as se:
                         raise ValueError(f"Syntax error in patch for {file_rel_path}: {se}")

                # Save changes
                with open(file_abs_path, "w", encoding="utf-8") as f:
                    f.write(new_content)
                applied.append(file_rel_path)
                
            return {"status": "success", "applied": applied, "backup": backup_path}
            
        except Exception as e:
            logger.error(f"Patching failed, reverting: {e}")
            # Revert from backup
            if os.path.exists(chip_path):
                shutil.rmtree(chip_path)
            shutil.copytree(backup_path, chip_path)
            return {"status": "error", "message": f"Patching failed (reverted): {e}"}
chip_editor = ChipEditor()
