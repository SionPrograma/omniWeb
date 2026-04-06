import sqlite3
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def apply_predictive_schema():
    print("OMNIWEB — BLOQUE: GOVERNANCE PREDICTIVE DRIFT ADVISOR SCHEMA.")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS governance_predictive_advisories (
                advisory_id TEXT PRIMARY KEY,
                target_domain TEXT,
                predictive_state TEXT,
                risk_projection TEXT,
                supporting_signals TEXT,
                historical_patterns TEXT,
                confidence REAL,
                rationale TEXT,
                recommended_action TEXT,
                is_active INTEGER DEFAULT 1,
                freshness TIMESTAMP,
                created_at TIMESTAMP
            )
            """)
            conn.commit()
    print("Schema applied successfully.")

if __name__ == "__main__":
    apply_predictive_schema()
