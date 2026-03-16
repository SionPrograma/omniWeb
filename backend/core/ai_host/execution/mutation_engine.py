import os
import shutil
import logging
import json
import time
import uuid
from typing import List, Dict, Optional, Any
from enum import Enum
from pydantic import BaseModel, Field
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class MutationType(str, Enum):
    CREATE_FILE = "CREATE_FILE"
    MODIFY_FILE = "MODIFY_FILE"
    PATCH_FILE = "PATCH_FILE"
    APPEND_FILE = "APPEND_FILE"
    DELETE_FILE = "DELETE_FILE"

class FileOperation(BaseModel):
    path: str
    op_type: MutationType
    content: Optional[str] = None
    patch_data: Optional[Dict] = None # For future complex patches

class MutationBatch(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: Optional[str] = None
    module_id: Optional[str] = None
    operations: List[FileOperation]
    origin: str = "Builder"
    timestamp: float = Field(default_factory=time.time)

class FileMutationEngine:
    """
    Handles atomic file operations across the codebase.
    Supports rollbacks and safety checks for Creator Mode.
    """
    def __init__(self):
        self.backup_root = "backend/data/backups/mutations"
        self.protected_paths = [".git", "node_modules", "backend/data/omniweb.db", ".env"]
        
        if not os.path.exists(self.backup_root):
            os.makedirs(self.backup_root, exist_ok=True)

    def _is_safe(self, path: str) -> bool:
        """Checks if the path is protected."""
        abs_path = os.path.abspath(path)
        for protected in self.protected_paths:
            if protected in abs_path or abs_path.endswith(protected):
                return False
        return True

    async def execute_batch(self, batch: MutationBatch) -> bool:
        """
        Executes a batch of file operations atomically.
        If any fails, rolls back the entire batch.
        """
        logger.info(f"[MUTATION_ENGINE] Executing batch {batch.id} with {len(batch.operations)} ops")
        
        # 1. Verification & Safety
        for op in batch.operations:
            if not self._is_safe(op.path):
                logger.error(f"[MUTATION_SAFETY_VIOLATION] Attempted to modify protected path: {op.path}")
                return False

        # 2. Preparation (Backups)
        backup_dir = os.path.join(self.backup_root, batch.id)
        os.makedirs(backup_dir, exist_ok=True)
        
        backups = {} # path -> backup_path
        created_paths = []

        try:
            for op in batch.operations:
                # If file exists and we are modifying/deleting, back it up
                if os.path.exists(op.path) and op.op_type != MutationType.CREATE_FILE:
                    backup_filename = f"{uuid.uuid4()}.bak"
                    backup_path = os.path.join(backup_dir, backup_filename)
                    shutil.copy2(op.path, backup_path)
                    backups[op.path] = backup_path
                elif not os.path.exists(op.path) and op.op_type == MutationType.CREATE_FILE:
                    created_paths.append(op.path)

            # 3. Execution
            for op in batch.operations:
                dir_name = os.path.dirname(op.path)
                if dir_name and not os.path.exists(dir_name):
                    os.makedirs(dir_name, exist_ok=True)

                if op.op_type == MutationType.CREATE_FILE or op.op_type == MutationType.MODIFY_FILE:
                    with open(op.path, "w", encoding="utf-8") as f:
                        f.write(op.content or "")
                
                elif op.op_type == MutationType.APPEND_FILE:
                    with open(op.path, "a", encoding="utf-8") as f:
                        f.write(op.content or "")

                elif op.op_type == MutationType.DELETE_FILE:
                    if os.path.exists(op.path):
                        os.remove(op.path)

                # TODO: Implement PATCH_FILE logic with diff/patch tools if needed
            
            # 4. Success Logging
            await self._log_mutation(batch, "SUCCESS")
            
            # 5. Hot Reload & Runtime Sync (Stage 15: Self-Edit Loop)
            from backend.core.runtime.self_edit_runtime import self_edit_runtime
            files = [op.path for op in batch.operations]
            sync_results = await self_edit_runtime.apply_runtime_sync(files, batch.id)
            
            if sync_results["status"] not in ["SUCCESS"]:
                logger.error(f"[MUTATION_ENGINE] Sync failed ({sync_results['status']}). Rolling back file changes.")
                await self._rollback(backups, created_paths)
                await self._log_mutation(batch, "FAILED_SYNC_ROLLBACK", error=sync_results.get("error"))
                return False, sync_results.get("reloaded_modules", [])
            
            return True, sync_results.get("reloaded_modules", [])

        except Exception as e:
            logger.error(f"[MUTATION_FAILED] Error in batch {batch.id}: {e}")
            # 6. Rollback
            await self._rollback(backups, created_paths)
            await self._log_mutation(batch, "ROLLED_BACK", error=str(e))
            return False, []

    async def _rollback(self, backups: Dict[str, str], created_paths: List[str]):
        """Restores files from backups and removes created files."""
        logger.warning("[MUTATION_ROLLBACK] Starting rollback sequence")
        
        # Restore modified/deleted
        for original_path, backup_path in backups.items():
            try:
                shutil.copy2(backup_path, original_path)
                logger.info(f"[ROLLBACK] Restored {original_path}")
            except Exception as e:
                logger.error(f"[ROLLBACK_ERROR] Failed to restore {original_path}: {e}")

        # Remove created
        for path in created_paths:
            try:
                if os.path.exists(path):
                    os.remove(path)
                    logger.info(f"[ROLLBACK] Removed {path}")
            except Exception as e:
                logger.error(f"[ROLLBACK_ERROR] Failed to remove {path}: {e}")

    async def _log_mutation(self, batch: MutationBatch, status: str, error: Optional[str] = None):
        """Records the result of a mutation batch in the database and Master Logbook."""
        try:
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO builder_mutations (
                        id, batch_id, task_id, module_id, files_affected, operations, status, error_message, origin, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()),
                    batch.id,
                    batch.task_id,
                    batch.module_id,
                    json.dumps([op.path for op in batch.operations]),
                    json.dumps([op.op_type.value for op in batch.operations]),
                    status,
                    error,
                    batch.origin,
                    time.time()
                ))
                conn.commit()
            
            # --- Phase 3: Hot Reload System - Evidence Capture ---
            from backend.core.master_logbook.manager import master_logbook_manager
            from backend.core.master_logbook.models import MasterLogbookEntry, EntryType, Priority, EntryStatus
            
            files_str = ", ".join([os.path.basename(op.path) for op in batch.operations])
            log_content = f"Mutación aplicada ({status}): {files_str}"
            if error:
                log_content += f" | Error: {error}"
                
            entry = MasterLogbookEntry(
                type=EntryType.AUTO_FIX if batch.origin == "Copilot" else EntryType.SYSTEM_EVENT,
                content=log_content,
                priority=Priority.MEDIUM if status == "SUCCESS" else Priority.HIGH,
                status=EntryStatus.DONE if status == "SUCCESS" else EntryStatus.OPEN,
                metadata={
                    "batch_id": batch.id,
                    "task_id": batch.task_id,
                    "files": [op.path for op in batch.operations],
                    "status": status,
                    "origin": batch.origin
                }
            )
            master_logbook_manager.add_entry(entry)

        except Exception as e:
            logger.error(f"[LOG_MUTATION_ERROR] {e}")

mutation_engine = FileMutationEngine()
