import sqlite3
import os

db_path = "backend/data/omniweb.db"
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute("SELECT filename FROM system_migrations").fetchall()
        print("Applied Migrations:")
        for row in rows:
            print(f"- {row['filename']}")
    except Exception as e:
        print(f"Error reading migrations: {e}")
    conn.close()
else:
    print(f"DB not found at {db_path}")
