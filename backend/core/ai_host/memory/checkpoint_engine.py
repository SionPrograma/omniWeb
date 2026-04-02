
import os
import shutil
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class MissionCheckpoint:
    def __init__(self, id: str, mission_id: str, label: str, db_path: str, files: List[str], timestamp: datetime):
        self.id = id
        self.mission_id = mission_id
        self.label = label
        self.db_path = db_path
        self.files = files
        self.timestamp = timestamp

class CheckpointEngine:
    def __init__(self):
        self.base_dir = os.path.abspath(os.path.join(os.getcwd(), ".mission_checkpoints"))
        os.makedirs(self.base_dir, exist_ok=True)

    def _get_mission_dir(self, mission_id: str) -> str:
        path = os.path.join(self.base_dir, f"mission_{mission_id}")
        os.makedirs(path, exist_ok=True)
        return path

    def create_snapshot(self, mission_id: str, label: str, targets: List[str] = []) -> str:
        """
        Creates a full state checkpoint of the mission.
        """
        checkpoint_id = f"cp_{int(datetime.now().timestamp())}"
        mission_dir = self._get_mission_dir(mission_id)
        cp_dir = os.path.join(mission_dir, checkpoint_id)
        os.makedirs(cp_dir, exist_ok=True)
        
        logger.info(f"[CHECKPOINT] Creating snapshot '{label}' for mission {mission_id}...")
        
        # 1. Database Backup
        db_backup_path = os.path.join(cp_dir, "state.db")
        db_manager.backup_db(db_backup_path)
        
        # 2. File Snapshots (Surgical)
        file_backups = []
        for target in targets:
            abs_path = os.path.abspath(target)
            if os.path.exists(abs_path) and os.path.isfile(abs_path):
                rel_path = os.path.relpath(abs_path, os.getcwd())
                # Use a safe flat name or structure
                safe_name = rel_path.replace(os.sep, "_").replace(":", "") + ".bak"
                dest = os.path.join(cp_dir, safe_name)
                shutil.copy2(abs_path, dest)
                file_backups.append({"original": abs_path, "backup": dest})
        
        # 3. Save Metadata
        metadata = {
            "id": checkpoint_id,
            "mission_id": mission_id,
            "label": label,
            "timestamp": datetime.now().isoformat(),
            "files": file_backups
        }
        with open(os.path.join(cp_dir, "metadata.json"), "w", encoding="utf-8") as f:
            import json
            json.dump(metadata, f, indent=4)
            
        logger.info(f"[CHECKPOINT] Checkpoint {checkpoint_id} created successfully.")
        return checkpoint_id

    def rollback(self, mission_id: str, checkpoint_id: str):
        """
        Performs a full rollback to the specified checkpoint.
        """
        mission_dir = self._get_mission_dir(mission_id)
        cp_dir = os.path.join(mission_dir, checkpoint_id)
        
        if not os.path.exists(cp_dir):
            raise FileNotFoundError(f"Checkpoint {checkpoint_id} not found for mission {mission_id}")
            
        logger.warning(f"[ROLLBACK] Restoring mission {mission_id} to checkpoint {checkpoint_id}...")
        
        # 1. Restore Files
        meta_path = os.path.join(cp_dir, "metadata.json")
        with open(meta_path, "r", encoding="utf-8") as f:
            import json
            metadata = json.load(f)
            
        for fb in metadata.get("files", []):
            orig = fb["original"]
            bak = fb["backup"]
            if os.path.exists(bak):
                logger.info(f"  Restoring file: {orig}")
                shutil.copy2(bak, orig)
        
        # 2. Restore Database
        db_backup_path = os.path.join(cp_dir, "state.db")
        db_manager.restore_db(db_backup_path)
        
        logger.info(f"[ROLLBACK] System state restored successfully.")
        return True

    def list_checkpoints(self, mission_id: str) -> List[Dict[str, Any]]:
        mission_dir = self._get_mission_dir(mission_id)
        cps = []
        import json
        for d in os.listdir(mission_dir):
            meta_path = os.path.join(mission_dir, d, "metadata.json")
            if os.path.exists(meta_path):
                with open(meta_path, "r", encoding="utf-8") as f:
                    cps.append(json.load(f))
        return sorted(cps, key=lambda x: x["timestamp"], reverse=True)

checkpoint_engine = CheckpointEngine()
