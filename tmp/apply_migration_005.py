import sqlite3
import os

db_path = 'backend/data/omniweb.db'
migration_path = 'backend/data/migrations/005_self_improvement.sql'

print(f"Applying migration from {migration_path} to {db_path}...")

with open(migration_path, 'r') as f:
    sql = f.read()

conn = sqlite3.connect(db_path, timeout=10)
try:
    conn.executescript(sql)
    conn.commit()
    print("Migration applied successfully.")
except Exception as e:
    print(f"Error: {e}")
finally:
    conn.close()
