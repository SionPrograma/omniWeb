import json
import logging
from typing import List, Optional, Dict, Any
from .models import MasterLogbookEntry, EntryType, Priority, EntryStatus, MasterLogbookFilter
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class MasterLogbookManager:
    """
    Handles persistence and retrieval of Master Logbook entries.
    """
    def __init__(self):
        self.table_name = "master_logbook"

    def add_entry(self, entry: MasterLogbookEntry) -> bool:
        try:
            with db_manager.get_connection() as conn:
                conn.execute(f"""
                    INSERT INTO {self.table_name} (
                        id, type, content, priority, chip_reference, status, author_role, timestamp, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    entry.id,
                    entry.type.value,
                    entry.content,
                    entry.priority.value,
                    entry.chip_reference,
                    entry.status.value,
                    entry.author_role,
                    entry.timestamp.isoformat(),
                    json.dumps(entry.metadata)
                ))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error adding logbook entry: {e}")
            return False

    def get_entries(self, filters: Optional[MasterLogbookFilter] = None, limit: int = 50) -> List[MasterLogbookEntry]:
        items = []
        query = f"SELECT * FROM {self.table_name}"
        where_clauses = []
        params = []

        if filters:
            if filters.type:
                where_clauses.append("type = ?")
                params.append(filters.type.value)
            if filters.priority:
                where_clauses.append("priority = ?")
                params.append(filters.priority.value)
            if filters.status:
                where_clauses.append("status = ?")
                params.append(filters.status.value)
            if filters.chip_reference:
                where_clauses.append("chip_reference = ?")
                params.append(filters.chip_reference)

        if where_clauses:
            query += " WHERE " + " AND ".join(where_clauses)
        
        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        try:
            with db_manager.get_connection() as conn:
                cursor = conn.execute(query, params)
                rows = cursor.fetchall()
                for row in rows:
                    items.append(MasterLogbookEntry(
                        id=row["id"],
                        type=EntryType(row["type"]),
                        content=row["content"],
                        priority=Priority(row["priority"]),
                        chip_reference=row["chip_reference"],
                        status=EntryStatus(row["status"]),
                        author_role=row["author_role"],
                        timestamp=row["timestamp"],
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                    ))
        except Exception as e:
            logger.error(f"Error retrieving logbook entries: {e}")

        return items

    def update_entry_status(self, entry_id: str, status: EntryStatus) -> bool:
        try:
            with db_manager.get_connection() as conn:
                conn.execute(f"UPDATE {self.table_name} SET status = ? WHERE id = ?", (status.value, entry_id))
                conn.commit()
            return True
        except Exception as e:
            logger.error(f"Error updating logbook entry status: {e}")
            return False

    def get_system_snapshot(self) -> Dict[str, Any]:
        """
        Gathers current system state info (Version, Git, Modules).
        """
        import subprocess
        from backend.core.config import settings
        from backend.core.module_registry import module_registry

        snapshot = {
            "version": settings.VERSION,
            "git_branch": "unknown",
            "last_commit": "unknown",
            "active_modules": settings.ACTIVE_MODULES,
            "module_inventory": [c["slug"] for c in module_registry.discover_all_chips()]
        }

        try:
            # Try to get git branch
            branch = subprocess.check_output(["git", "rev-parse", "--abbrev-ref", "HEAD"], text=True).strip()
            snapshot["git_branch"] = branch
            
            # Try to get last commit
            commit = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
            snapshot["last_commit"] = commit[:8]
        except Exception:
            # Not a git repo or git not found
            pass

        return snapshot

master_logbook_manager = MasterLogbookManager()
