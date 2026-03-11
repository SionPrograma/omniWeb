import logging
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .memory_models import MemoryEntry, MemoryLink

logger = logging.getLogger(__name__)

class MemoryStore:
    """
    Persistence layer for Long Term Memory using SQLite.
    """
    def save_memory(self, memory: MemoryEntry) -> int:
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    cursor = conn.execute(
                        """
                        INSERT INTO long_term_memories 
                        (memory_type, title, summary, content, source_chip, source_session, importance_score, confidence_score)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            memory.memory_type, memory.title, memory.summary, 
                            memory.content, memory.source_chip, memory.source_session,
                            memory.importance_score, memory.confidence_score
                        )
                    )
                    conn.commit()
                    return cursor.lastrowid
            except Exception as e:
                logger.error(f"MemoryStore: Failed to save memory: {e}")
                return -1

    def save_link(self, link: MemoryLink):
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO memory_links (memory_id, related_type, related_id, relationship)
                        VALUES (?, ?, ?, ?)
                        """,
                        (link.memory_id, link.related_type, link.related_id, link.relationship)
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"MemoryStore: Failed to save link: {e}")

    def get_memories(self, memory_type: Optional[str] = None, limit: int = 20) -> List[MemoryEntry]:
        query = "SELECT * FROM long_term_memories"
        params = []
        if memory_type:
            query += " WHERE memory_type = ?"
            params.append(memory_type)
        
        query += " ORDER BY last_accessed_at DESC LIMIT ?"
        params.append(limit)

        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    rows = conn.execute(query, params).fetchall()
                    return [MemoryEntry(**dict(row)) for row in rows]
            except Exception as e:
                logger.error(f"MemoryStore: Failed to fetch memories: {e}")
                return []

    def get_links(self, memory_id: int) -> List[MemoryLink]:
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM memory_links WHERE memory_id = ?", (memory_id,)).fetchall()
                    return [MemoryLink(**dict(row)) for row in rows]
            except Exception as e:
                logger.error(f"MemoryStore: Failed to fetch links: {e}")
                return []

memory_store = MemoryStore()
