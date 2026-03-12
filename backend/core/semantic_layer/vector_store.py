import json
import logging
from typing import List, Optional
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .embedding_models import VectorEntry

logger = logging.getLogger(__name__)

class VectorStore:
    """
    Handles storage and retrieval of vector embeddings.
    Integrates with the main OmniWeb SQLite database.
    Schema maintained via migration 009.
    """
    def upsert_embedding(self, entry: VectorEntry):
        """Creates or updates a semantic embedding entry."""
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
        """Retrieves all indexed embeddings from the database."""
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

    def get_all_ids(self) -> set:
        """Returns a set of all indexed node_ids for fast delta calculation."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT node_id FROM semantic_embeddings").fetchall()
                return {row["node_id"] for row in rows}

    def delete_embedding(self, node_id: str):
        """Removes an embedding by node_id."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("DELETE FROM semantic_embeddings WHERE node_id = ?", (node_id,))
                conn.commit()

    def find_by_type(self, source_type: str) -> List[VectorEntry]:
        """Fast lookup by source type using index."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM semantic_embeddings WHERE source_type = ?", (source_type,)).fetchall()
                return [VectorEntry(
                    node_id=row["node_id"],
                    source_type=row["source_type"],
                    embedding=json.loads(row["embedding"]),
                    text_content=row["text_content"],
                    timestamp=row["timestamp"]
                ) for row in rows]

vector_store = VectorStore()
