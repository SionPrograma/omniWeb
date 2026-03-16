import importlib
import sys
import os
import logging
import uuid
import json
from typing import List, Optional
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class HotReloadEngine:
    """
    Handles dynamic reloading of Python modules modified by the FileMutationEngine.
    Ensures safe operations by skipping protected core modules.
    """
    def __init__(self):
        self.protected_modules = [
            "backend.core.database",
            "backend.core.config",
            "backend.core.security",
            "backend.core.auth",
            "backend.core.master_logbook",
            "backend.main"
        ]

    def _path_to_module(self, file_path: str) -> Optional[str]:
        """Converts a file path to a Python module name relative to the working directory."""
        try:
            cwd = os.getcwd()
            # Handle absolute paths by making them relative to CWD
            if os.path.isabs(file_path):
                try:
                    rel_path = os.path.relpath(file_path, cwd)
                except ValueError:
                    # Likely on a different drive on Windows
                    return None
            else:
                rel_path = file_path
                
            if not rel_path.endswith(".py"):
                if any(rel_path.endswith(ext) for ext in [".html", ".css", ".js"]):
                    return f"frontend_asset::{rel_path}"
                return None
                
            # Normalize and remove .py extension
            norm_path = os.path.normpath(rel_path)
            if norm_path.endswith("__init__.py"):
                base = os.path.dirname(norm_path)
            else:
                base = norm_path[:-3]
            
            # Map directory separators to dots
            module_name = base.replace(os.sep, ".").replace("/", ".")
            module_name = module_name.strip(".")
            
            return module_name
        except Exception as e:
            logger.error(f"[HOT_RELOAD_PATH_ERROR] {e}")
            return None

    async def notify_changes(self, file_paths: List[str]):
        """
        Triggered after successful mutations. Evaluates and reloads affected modules.
        Returns a summary of reload actions.
        """
        logger.info(f"[HOT_RELOAD] Evaluating changes in {len(file_paths)} files")
        
        results = []
        reloaded_count = 0
        failed_count = 0
        
        # Unique modules to avoid double reloading if multiple files in same module changed
        targets = set()
        for path in file_paths:
            module_name = self._path_to_module(path)
            if module_name:
                targets.add((module_name, path))

        for module_name, trigger_file in targets:
            # Check protection
            is_protected = any(module_name == protected or module_name.startswith(protected + ".") 
                               for protected in self.protected_modules)
            
            if is_protected:
                logger.warning(f"[HOT_RELOAD] Skipping protected module: {module_name}")
                results.append({"module": module_name, "status": "PROTECTED"})
                continue
            
            if module_name.startswith("frontend_asset::"):
                asset_path = module_name.split("::")[1]
                logger.info(f"[HOT_RELOAD] Frontend asset changed: {asset_path}")
                results.append({"module": asset_path, "status": "RELOADED"})
                continue
                
            # Check if loaded
            if module_name in sys.modules:
                success = await self.reload_module(module_name, [trigger_file])
                if success:
                    reloaded_count += 1
                    results.append({"module": module_name, "status": "RELOADED"})
                else:
                    failed_count += 1
                    results.append({"module": module_name, "status": "FAILED"})
            else:
                # Not loaded, so nothing to reload. New files will be picked up on first import.
                results.append({"module": module_name, "status": "NOT_LOADED"})
                
        logger.info(f"[HOT_RELOAD] Finished. Reloaded: {reloaded_count}, Failed: {failed_count}")
        return results

    async def reload_module(self, module_name: str, trigger_files: List[str]) -> bool:
        """Safely reloads a specific module using importlib."""
        try:
            logger.info(f"[HOT_RELOAD] Reloading {module_name}...")
            if module_name in sys.modules:
                importlib.invalidate_caches()
                mod = sys.modules[module_name]
                try:
                    importlib.reload(mod)
                except Exception as e:
                    logger.warning(f"[HOT_RELOAD] Standard reload failed for {module_name}: {e}. Trying fallback.")
                    # Fallback to manual exec if reload hits a transient error or bad state
                    with open(mod.__file__, "r", encoding="utf-8") as f:
                        code = compile(f.read(), mod.__file__, "exec")
                        exec(code, mod.__dict__)
                
                await self._log_reload(module_name, trigger_files, "SUCCESS")
                return True
            return False
        except Exception as e:
            error_msg = str(e)
            logger.error(f"[HOT_RELOAD] Failed to reload {module_name}: {error_msg}")
            await self._log_reload(module_name, trigger_files, "FAILED", error=error_msg)
            return False

    async def _log_reload(self, module_name: str, files: List[str], status: str, error: Optional[str] = None):
        try:
            from backend.core.permissions import set_chip_context
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO hot_reload_logs (id, module_name, files_changed, status, error_message)
                        VALUES (?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), module_name, json.dumps(files), status, error
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"[HOT_RELOAD_LOG_ERROR] {e}")

hot_reload_engine = HotReloadEngine()
