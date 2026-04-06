import sqlite3
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def apply_atlas_schema():
    print("OMNIWEB — BLOQUE: WISDOM ATLAS SCHEMA.")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_wisdom_atlas_nodes (
                node_id TEXT PRIMARY KEY,
                node_type TEXT NOT NULL, -- LEARNING, AUTOPSY, DECISION, REPLAY_SYNC, CONTEXT_MAPPING, TACTIC
                source_ref_type TEXT, -- Table name or type
                source_ref_id TEXT,
                project_id TEXT,
                affected_domains TEXT,
                title TEXT,
                summary TEXT,
                confidence REAL,
                reusability_score REAL,
                status_band TEXT, -- CONFIRMED, EXPERIMENTAL, CONTRADICTED, DEGRADED
                related_refs TEXT, -- JSON list of node_ids
                evidence_refs TEXT, -- JSON map of sources
                freshness REAL, -- Decay factor
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            """)
            conn.commit()
    print("Schema applied successfully.")

if __name__ == "__main__":
    apply_atlas_schema()
