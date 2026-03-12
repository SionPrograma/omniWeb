import json
import logging
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager
from .embedding_models import VectorEntry, SemanticSearchResult

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Handles storage and retrieval of vector embeddings.
    Integrates with the main OmniWeb SQLite database.
    """
    def __init__(self):
        self._init_table()

    def _init_table(self):
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS semantic_embeddings (
                        node_id TEXT PRIMARY KEY,
                        source_type TEXT NOT NULL,
                        embedding TEXT NOT NULL,
                        text_content TEXT,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                conn.commit()

    def upsert_embedding(self, entry: VectorEntry):
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO semantic_embeddings (node_id, source_type, embedding, text_content)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(node_id) DO UPDATE SET
                        embedding = excluded.embedding,
                        text_content = excluded.text_content,
                        timestamp = CURRENT_TIMESTAMP
                """, (entry.node_id, entry.source_type, json.dumps(entry.embedding), entry.text_content))
                conn.commit()

    def get_all_embeddings(self) -> List[VectorEntry]:
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM semantic_embeddings").fetchall()
                return [VectorEntry(
                    node_id=row["node_id"],
                    source_type=row["source_type"],
                    embedding=json.loads(row["embedding"]),
                    text_content=row["text_content"],
                    timestamp=row["timestamp"]
                ) for row in rows]

    def delete_embedding(self, node_id: str):
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("DELETE FROM semantic_embeddings WHERE node_id = ?", (node_id,))
                conn.commit()

vector_store = VectorStore()
