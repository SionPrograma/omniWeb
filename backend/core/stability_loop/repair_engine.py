import logging
import os
import shutil

logger = logging.getLogger(__name__)

class RepairEngine:
    """
    Attempts automated repair when a failure is detected.
    """
    def __init__(self):
        pass

    async def attempt_repair(self, failure_details: dict) -> bool:
        """
        Main entry point for repairs.
        """
        logger.warning(f"Repair Engine triggered with failures: {failure_details}")
        
        repaired = False
        
        # 1. Check if it's a DB issue
        if not failure_details.get("database", True):
             repaired = self._repair_db()
             
        # 2. Check if it's a chip loading issue
        if not failure_details.get("chips", True):
             repaired = self._repair_registry()

        return repaired

    def _repair_db(self) -> bool:
        logger.info("Attempting DB repair: refreshing migrations.")
        try:
            from backend.core.database import db_manager
            db_manager.run_migrations()
            return True
        except Exception as e:
            logger.error(f"DB repair failed: {e}")
            return False

    def _repair_registry(self) -> bool:
        logger.info("Attempting Registry repair: reloading modules.")
        try:
            from backend.core.module_registry import module_registry
            module_registry.discover_all_chips()
            return True
        except Exception as e:
            logger.error(f"Registry repair failed: {e}")
            return False

    def rollback_file(self, target_path: str, backup_path: str) -> bool:
        """Restores a file from backup."""
        if not os.path.exists(backup_path):
            logger.error(f"Cannot rollback: backup not found at {backup_path}")
            return False
        
        try:
            shutil.copy2(backup_path, target_path)
            logger.info(f"Rollback successful: {target_path} restored.")
            return True
        except Exception as e:
            logger.error(f"Rollback failed for {target_path}: {e}")
            return False

repair_engine = RepairEngine()
