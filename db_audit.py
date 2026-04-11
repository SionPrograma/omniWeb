
import sqlite3
import os

db_path = "backend/data/omniweb.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

def get_tables():
    return [r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")]

def get_cols(table):
    c = conn.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in c.fetchall()]

def get_applied_migrations():
    try:
        return [r[0] for r in conn.execute("SELECT filename FROM system_migrations")]
    except: return []

print("=== DB AUDIT RECOVERY ===")
print(f"Tables: {get_tables()}")
print(f"Applied Migrations: {get_applied_migrations()}")

# Check common suspects from 113+
if 'governance_wisdom_feedback' in get_tables():
    print(f"governance_wisdom_feedback: EXISITS")

if 'post_mission_syncs' in get_tables() or 'governance_post_mission_syncs' in get_tables():
    print(f"post_mission_sync: EXISTS")

# Check specifically for 113 columns
for t in ["roadmap_branches", "mission_handoffs", "system_missions"]:
    if 'source_draft_id' in get_cols(t):
        print(f"Table {t} HAS source_draft_id")

conn.close()
