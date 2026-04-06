import sqlite3
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def apply_graph_schema():
    print("OMNIWEB — BLOQUE: WISDOM GRAPH SCHEMA.")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_wisdom_graph_edges (
                edge_id TEXT PRIMARY KEY,
                source_node_id TEXT NOT NULL,
                target_node_id TEXT NOT NULL,
                relation_type TEXT NOT NULL, -- DERIVED_FROM, CONFIRMED_BY, CONTRADICTED_BY, REUSED_IN, RELATED_DOMAIN, SAME_PROJECT, CONTEXT_MATCH, BASELINE_SOURCE
                strength REAL DEFAULT 1.0,
                rationale TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(source_node_id, target_node_id, relation_type)
            )
            """)
            conn.commit()
    print("Graph schema applied successfully.")

if __name__ == "__main__":
    apply_graph_schema()
