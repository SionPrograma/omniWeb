import sqlite3
import os

DB_PATH = "backend/data/omniweb.db"

def setup_risk_override_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Risk Overrides Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS governance_risk_overrides (
        override_id TEXT PRIMARY KEY,
        recommendation_id TEXT NOT NULL,
        target_id TEXT NOT NULL,
        override_type TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        rationale TEXT NOT NULL,
        conditions TEXT,
        expiry_at TEXT,
        created_at TEXT NOT NULL
    )
    """)
    
    # Index for lookup by recommendation or target
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_override_target ON governance_risk_overrides(target_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_override_rec ON governance_risk_overrides(recommendation_id)")
    
    conn.commit()
    conn.close()
    print("✅ Governance Risk Overrides table initialized.")

if __name__ == "__main__":
    setup_risk_override_db()
