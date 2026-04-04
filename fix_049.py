import sqlite3
import os

db_path = "backend/data/omniweb.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        # Mark 049 as applied to avoid duplicate column error
        conn.execute("INSERT INTO system_migrations (filename) VALUES ('049_resource_locks_status.sql')")
        conn.commit()
        print("Successfully marked 049_resource_locks_status.sql as applied.")
    except Exception as e:
        print(f"Failed to mark 049 as applied (might already be there or table error): {e}")
    conn.close()
