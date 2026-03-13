import sqlite3
import os

db_path = "backend/data/omniweb.db"
if not os.path.exists(db_path):
    print(f"DB not found at {db_path}")
    # Try current directory too if running from a different context
    db_path = "omniweb.db"
    if not os.path.exists(db_path):
        print(f"DB not found at {db_path} either.")
        # Check if we are in backend/
        db_path = "data/omniweb.db"
        if not os.path.exists(db_path):
            print("Could not find db.")
            exit(1)

print(f"Using DB at: {db_path}")
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

print("Applied Migrations:")
try:
    cursor.execute("SELECT filename FROM system_migrations")
    for row in cursor.fetchall():
        print(f"- {row['filename']}")
except Exception as e:
    print(f"Error reading migrations: {e}")

print("\nTables:")
try:
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    for row in cursor.fetchall():
        print(f"- {row['name']}")
except Exception as e:
    print(f"Error reading tables: {e}")

conn.close()
