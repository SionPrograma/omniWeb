import sqlite3
import os

db_path = 'backend/database.sqlite'
migration_path = 'backend/data/migrations/108_governance_fusion_snapshots.sql'

with open(migration_path, 'r') as f:
    sql = f.read()

conn = sqlite3.connect(db_path)
try:
    conn.executescript(sql)
    conn.commit()
    print("Migration 108 successful.")
except Exception as e:
    print(f"Migration 108 failed: {e}")
finally:
    conn.close()
