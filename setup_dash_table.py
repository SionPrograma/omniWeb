from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def setup_advisory_table():
    sql = """
    CREATE TABLE IF NOT EXISTS governance_advisories (
        advisory_id TEXT PRIMARY KEY,
        source_pattern_id TEXT NOT NULL,
        advisory_state TEXT DEFAULT 'PENDING',
        handoff_id TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute(sql)
            conn.commit()
    print("Table governance_advisories setup complete.")

if __name__ == "__main__":
    setup_advisory_table()
