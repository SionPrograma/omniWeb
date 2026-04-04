import sqlite3
import os

db_path = 'backend/data/omniweb.db'
if not os.path.exists(db_path):
    print(f"ERROR: DB not found at {db_path}")
    exit(1)

conn = sqlite3.connect(db_path)
cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cursor.fetchall()]
print(f"Tables found: {tables}")

if 'system_locks' in tables:
    print("Table system_locks exists.")
    cursor = conn.execute("PRAGMA table_info(system_locks)")
    cols = [r[1] for r in cursor.fetchall()]
    print(f"Columns in system_locks: {cols}")
else:
    print("Table system_locks DOES NOT exist.")

conn.close()
