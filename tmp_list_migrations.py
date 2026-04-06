from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def list_migrations():
    with set_chip_context('core'):
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT filename FROM system_migrations").fetchall()
            print("Applied Migrations:")
            for r in rows:
                print(f"- {r['filename']}")

if __name__ == "__main__":
    list_migrations()
