import json
import logging
from typing import List, Optional, Dict, Any
from .models import AdminOperation, AISuggestion, SuggestionStatus, SystemCheckpoint
from backend.core.database import db_manager
from backend.core.config import settings

logger = logging.getLogger(__name__)

class AdminManager:
    """
    Manages operational logs, AI suggestions review, and system rollbacks.
    """

    def log_operation(self, admin_id: str, op_type: str, target: str, details: Dict[str, Any]):
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO admin_operations (admin_id, operation_type, target_resource, details)
                VALUES (?, ?, ?, ?)
            """, (admin_id, op_type, target, json.dumps(details)))
            conn.commit()
            logger.info(f"Admin Operation Logged: {op_type} by {admin_id} on {target}")

    def list_operations(self, limit: int = 50) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM admin_operations ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            return [dict(row) for row in rows]

    def add_ai_suggestion(self, suggestion: AISuggestion):
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO ai_suggestions (id, suggestion_type, content, severity, status)
                VALUES (?, ?, ?, ?, ?)
            """, (suggestion.id, suggestion.suggestion_type, json.dumps(suggestion.content), 
                  suggestion.severity, suggestion.status))
            conn.commit()

    def review_suggestion(self, suggestion_id: str, admin_id: str, status: SuggestionStatus, notes: str = ""):
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE ai_suggestions 
                SET status = ?, reviewer_id = ?, review_notes = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (status, admin_id, notes, suggestion_id))
            conn.commit()
            self.log_operation(admin_id, f"SUGGESTION_{status}", suggestion_id, {"notes": notes})

    def get_pending_suggestions(self) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM ai_suggestions WHERE status = 'PENDING'").fetchall()
            return [dict(row) for row in rows]

    async def list_checkpoints(self) -> List[Dict[str, Any]]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM system_checkpoints ORDER BY created_at DESC").fetchall()
            return [dict(row) for row in rows]

    def create_checkpoint(self, creator_id: str, label: str) -> str:
        # Security check (creator only)
        if creator_id != settings.CREATOR_ID:
             raise PermissionError("Checkpoint creation requires Creator authority")

        # 1. DB Backup
        backup_path = db_manager.backup_db()
        
        # 2. Record Checkpoint
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO system_checkpoints (creator_id, label, db_backup_path)
                VALUES (?, ?, ?)
            """, (creator_id, label, backup_path))
            conn.commit()
            
        self.log_operation(creator_id, "CREATE_CHECKPOINT", label, {"backup_path": backup_path})
        logger.info(f"System Checkpoint Created: {label} by {creator_id}")
        return backup_path

    def rollback_to_checkpoint(self, checkpoint_id: int, creator_id: str):
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM system_checkpoints WHERE id = ?", (checkpoint_id,)).fetchone()
            if not row:
                raise ValueError("Checkpoint not found")
            
            # Security check (creator only)
            if creator_id != settings.CREATOR_ID:
                 raise PermissionError("Rollback requires Creator authority")

            backup_path = row["db_backup_path"]
            db_manager.restore_db(backup_path)
            
            self.log_operation(creator_id, "ROLLBACK", f"checkpoint_{checkpoint_id}", {"label": row["label"]})
            logger.warning(f"SYSTEM ROLLBACK EXECUTED by {creator_id} to checkpoint {checkpoint_id}")

admin_manager = AdminManager()
