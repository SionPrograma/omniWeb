from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def db_audit():
    with set_chip_context('core'):
        with db_manager.get_connection() as conn:
            # 1. Check columns
            print("\nColumns in governance_risk_overrides:")
            rows = conn.execute("PRAGMA table_info(governance_risk_overrides)").fetchall()
            for r in rows:
                print(f"- {r['name']}")
                
            # 2. Check if relief proposals table exists
            print("\nTables in DB:")
            tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
            for t in tables:
                print(f"- {t['name']}")

if __name__ == "__main__":
    db_audit()
