import difflib
import os
import json
import time
import uuid
import logging
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .mutation_engine import MutationBatch, MutationType
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class FileDiff(BaseModel):
    path: str
    op_type: str
    diff_text: str
    added_lines: int
    removed_lines: int

class PatchPreview(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    module_id: str
    batch: MutationBatch
    diffs: List[FileDiff]
    status: str = "PENDING"
    gate_decision: Optional[Dict[str, Any]] = None
    timestamp: float = Field(default_factory=time.time)

class PatchPreviewEngine:
    """
    Generates and manages diff previews for proposed mutations.
    """
    def generate_preview(self, task_id: str, module_id: str, batch: MutationBatch) -> PatchPreview:
        logger.info(f"[PATCH_PREVIEW] Generating preview for batch {batch.id}")
        from ..shadow_swarm.approval_gate import approval_gate, GateStatus
        
        # Governance Evaluation (Bloque 3)
        targets = [op.path for op in batch.operations]
        decision = approval_gate.execute_governance_check(
            intent=f"Mutación en {len(targets)} archivo(s)",
            targets=targets,
            action_type="mutation"
        )
        
        if decision.status == GateStatus.EXTREME:
            raise PermissionError(f"BLOQUEO SEGURIDAD: {decision.blocking_reason}")

        file_diffs = []
        for op in batch.operations:
            existing_content = ""
            if os.path.exists(op.path):
                try:
                    with open(op.path, "r", encoding="utf-8") as f:
                        existing_content = f.read()
                except Exception as e:
                    logger.error(f"[PREVIEW_READ_ERROR] {op.path}: {e}")
                    existing_content = f"(Error reading file: {e})"

            proposed_content = op.content or ""
            
            # Generate diff
            diff = list(difflib.unified_diff(
                existing_content.splitlines(keepends=True),
                proposed_content.splitlines(keepends=True),
                fromfile=f"a/{op.path}",
                tofile=f"b/{op.path}",
                lineterm=""
            ))
            
            diff_text = "".join(diff)
            added = len([line for line in diff if line.startswith('+') and not line.startswith('+++')])
            removed = len([line for line in diff if line.startswith('-') and not line.startswith('---')])

            file_diffs.append(FileDiff(
                path=op.path,
                op_type=op.op_type.value,
                diff_text=diff_text,
                added_lines=added,
                removed_lines=removed
            ))

        preview = PatchPreview(
            task_id=task_id,
            module_id=module_id,
            batch=batch,
            diffs=file_diffs,
            gate_decision=decision.dict()
        )
        
        self._save_preview(preview)
        return preview

    def _save_preview(self, preview: PatchPreview):
        try:
            with db_manager.get_connection(internal=True) as conn:
                conn.execute("""
                    INSERT INTO builder_patch_previews (id, task_id, module_id, batch_data, diff_data, status, timestamp)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    preview.id, preview.task_id, preview.module_id,
                    preview.batch.json(),
                    json.dumps([d.dict() for d in preview.diffs]),
                    preview.status, preview.timestamp
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"[PREVIEW_SAVE_ERROR] {e}")

    async def get_preview(self, preview_id: str) -> Optional[PatchPreview]:
        try:
            with db_manager.get_connection(internal=True) as conn:
                row = conn.execute("SELECT * FROM builder_patch_previews WHERE id = ?", (preview_id,)).fetchone()
                if not row: return None
                
                batch_data = json.loads(row["batch_data"])
                diff_data = json.loads(row["diff_data"])
                
                return PatchPreview(
                    id=row["id"],
                    task_id=row["task_id"],
                    module_id=row["module_id"],
                    batch=MutationBatch(**batch_data),
                    diffs=[FileDiff(**d) for d in diff_data],
                    status=row["status"],
                    timestamp=row["timestamp"]
                )
        except Exception as e:
            logger.error(f"[PREVIEW_LOAD_ERROR] {e}")
            return None

    async def decide(self, preview_id: str, approved: bool, author: str = "creator") -> bool:
        status = "APPROVED" if approved else "REJECTED"
        try:
            with db_manager.get_connection(internal=True) as conn:
                conn.execute("""
                    UPDATE builder_patch_previews 
                    SET status = ?, decision_by = ? 
                    WHERE id = ?
                """, (status, author, preview_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"[PREVIEW_DECISION_ERROR] {e}")
            return False

patch_preview_engine = PatchPreviewEngine()
