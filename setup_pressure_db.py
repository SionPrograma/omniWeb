import sqlite3
import os

DB_PATH = "backend/data/omniweb.db"

def setup_pressure_timeline():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Pressure Events Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS governance_pressure_events (
        event_id TEXT PRIMARY KEY,
        target_id TEXT NOT NULL,
        event_type TEXT NOT NULL,
        source_advisory_id TEXT NOT NULL,
        risk_level TEXT NOT NULL,
        creator_decision TEXT,
        rationale TEXT,
        timestamp TEXT NOT NULL
    )
    """)
    
    # Index for fast retrieval by target
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_pressure_target ON governance_pressure_events(target_id)")
    
    conn.commit()
    conn.close()
    print("✅ Governance Pressure Events table initialized.")

if __name__ == "__main__":
    setup_pressure_timeline()
