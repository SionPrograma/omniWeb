
import sqlite3
import os

db_path = "backend/data/omniweb.db"
if not os.path.exists(db_path):
    print(f"DB not found: {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
try:
    rows = conn.execute("SELECT * FROM system_migrations ORDER BY id DESC LIMIT 20").fetchall()
    print("LAST 20 MIGRATIONS:")
    for r in rows:
        print(f"{r['id']} | {r['filename']} | {r['applied_at']}")
except Exception as e:
    print(f"Error: {e}")
conn.close()
