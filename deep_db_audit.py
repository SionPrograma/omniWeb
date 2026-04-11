
import sqlite3
db_path = "backend/data/omniweb.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

def has_table(name):
    return conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone() is not None

def has_col(table, col):
    try:
        c = conn.execute(f"PRAGMA table_info({table})")
        return col in [r[1] for r in c.fetchall()]
    except: return False

print("=== DEEP AUDIT ===")
# 115: mission_feedback_columns
print(f"115/116 check (system_missions.preconditions_ok): {has_col('system_missions', 'preconditions_ok')}")

# 120: wisdom_multi_context_harvester
print(f"120 check (governance_wisdom_harvests): {has_table('governance_wisdom_harvests')}")

# 121: catalyst_settings
# check if 'CATALYST_ENABLED' exists in governance_engine_parameters
params = conn.execute("SELECT param_key FROM governance_engine_parameters WHERE param_key LIKE 'CATALYST_%'").fetchall()
print(f"121 check (Catalyst params): {[r[0] for r in params]}")

# 124: draft_steps
print(f"124 check (governance_mission_auto_drafts.suggested_steps): {has_col('governance_mission_auto_drafts', 'suggested_steps')}")

# 125: wisdom_sync_proposals
print(f"125 check (governance_wisdom_sync_proposals): {has_table('governance_wisdom_sync_proposals')}")

# 126: sync_catalyst
print(f"126 check (governance_post_mission_syncs.catalyst_trace_id): {has_col('governance_post_mission_syncs', 'catalyst_trace_id')}")

conn.close()
