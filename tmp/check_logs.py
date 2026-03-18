import sqlite3
import os

db_path = 'backend/data/omniweb.db'
if not os.path.exists(db_path):
    print(f"Error: Database {db_path} not found.")
    exit(1)

conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
try:
    cursor = conn.execute("SELECT * FROM hot_reload_logs ORDER BY timestamp DESC LIMIT 5")
    rows = cursor.fetchall()
    for row in rows:
        print(dict(row))
except Exception as e:
    print(f"Error executing query: {e}")
finally:
    conn.close()
