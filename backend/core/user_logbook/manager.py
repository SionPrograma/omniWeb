import os
import json
import logging
from typing import List, Optional
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .models import UserLogbookEntry, UserEntryType

logger = logging.getLogger(__name__)

class UserLogbookManager:
    def __init__(self):
        self.workspace_root = "user_workspace"

    def _get_user_logbook_dir(self, user_id: str) -> str:
        path = os.path.join(self.workspace_root, user_id, "logbook")
        os.makedirs(path, exist_ok=True)
        return path

    def add_entry(self, entry: UserLogbookEntry):
        """
        Saves entry to DB and replicates to user workspace.
        """
        from backend.core.permissions import enforce_permission, USER_LOGBOOK_ACCESS
        enforce_permission(USER_LOGBOOK_ACCESS)
        # 1. Save to DB
        metadata_json = json.dumps(entry.metadata)
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO user_logbooks (id, user_id, entry_type, content, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (entry.id, entry.user_id, entry.entry_type.value, entry.content, 
                     entry.timestamp.isoformat(), metadata_json)
                )
                conn.commit()

        # 2. Replicate to Workspace (JSON parity)
        log_dir = self._get_user_logbook_dir(entry.user_id)
        filename = f"{entry.timestamp.strftime('%Y%m%d_%H%M%S')}_{entry.id[:8]}.json"
        with open(os.path.join(log_dir, filename), "w", encoding="utf-8") as f:
            json.dump(entry.model_dump(mode='json'), f, indent=2)

        logger.info(f"User Logbook Entry created for {entry.user_id}: {entry.entry_type}")

        # 3. Trigger Graph Node Creation (Phase 18)
        try:
            from backend.core.user_graph.engine import user_graph_engine
            from backend.core.user_graph.models import GraphNode
            node = GraphNode(
                user_id=entry.user_id,
                entry_id=entry.id,
                node_type=entry.entry_type.value,
                content=entry.content,
                timestamp=entry.timestamp,
                metadata=entry.metadata
            )
            user_graph_engine.save_node(node)
        except Exception as e:
            logger.error(f"UserLogbookManager: Failed to sync to graph: {e}")

    def list_entries(self, user_id: str, entry_type: Optional[UserEntryType] = None, limit: int = 50) -> List[UserLogbookEntry]:
        from backend.core.permissions import enforce_permission, USER_LOGBOOK_ACCESS
        enforce_permission(USER_LOGBOOK_ACCESS)
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                query = "SELECT * FROM user_logbooks WHERE user_id = ?"
                params = [user_id]
                
                if entry_type:
                    query += " AND entry_type = ?"
                    params.append(entry_type.value)
                
                query += " ORDER BY timestamp DESC LIMIT ?"
                params.append(limit)
                
                rows = conn.execute(query, params).fetchall()
                
                entries = []
                for row in rows:
                    entries.append(UserLogbookEntry(
                        id=row["id"],
                        user_id=row["user_id"],
                        entry_type=UserEntryType(row["entry_type"]),
                        content=row["content"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                    ))
                return entries

    def search_entries(self, user_id: str, search_query: str) -> List[UserLogbookEntry]:
        from backend.core.permissions import enforce_permission, USER_LOGBOOK_ACCESS
        enforce_permission(USER_LOGBOOK_ACCESS)
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM user_logbooks WHERE user_id = ? AND content LIKE ? ORDER BY timestamp DESC",
                    (user_id, f"%{search_query}%")
                ).fetchall()
                
                return [
                    UserLogbookEntry(
                        id=row["id"],
                        user_id=row["user_id"],
                        entry_type=UserEntryType(row["entry_type"]),
                        content=row["content"],
                        timestamp=datetime.fromisoformat(row["timestamp"]),
                        metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                    ) for row in rows
                ]

logbook_manager = UserLogbookManager()
