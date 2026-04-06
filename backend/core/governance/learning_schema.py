import sqlite3
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def apply_learning_schema():
    print("OMNIWEB — BLOQUE: GOVERNANCE LEARNING SURFACE SCHEMA.")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_learning_items (
                learning_item_id TEXT PRIMARY KEY,
                learning_type TEXT,
                target_domain TEXT,
                lesson_summary TEXT,
                recommended_behavior TEXT,
                confidence REAL,
                supporting_evidence TEXT,
                is_antipattern INTEGER,
                occurrence_count INTEGER,
                project_id TEXT DEFAULT 'PROJECT_OMNIWEB_PROD',
                freshness TIMESTAMP,
                created_at TIMESTAMP
            )
            """)
            conn.commit()
    print("Schema applied successfully.")

if __name__ == "__main__":
    apply_learning_schema()
