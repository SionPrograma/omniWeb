
import sqlite3
import os

db_path = "backend/data/omniweb.db"
conn = sqlite3.connect(db_path)
conn.row_factory = sqlite3.Row

missing = [
    "113_wisdom_feedback_traceability.sql",
    "114_wisdom_feedback_engine_hardening.sql",
    "115_mission_feedback_columns.sql",
    "116_wisdom_action_bridge.sql",
    "117_roadmap_optimizer.sql",
    "118_roadside_assistant.sql",
    "119_post_mission_wisdom_sync.sql",
    "120_wisdom_multi_context_harvester.sql",
    "121_catalyst_settings.sql",
    "122_catalyst_memory_bridge.sql",
    "123_catalyst_spec_translator.sql",
    "124_draft_steps.sql",
    "125_wisdom_sync_proposals.sql",
    "126_sync_catalyst.sql"
]

print("=== DB RECOVERY EXECUTION ===")
for m in missing:
    try:
        conn.execute("INSERT OR IGNORE INTO system_migrations (filename) VALUES (?)", (m,))
        print(f"Registered {m} as applied.")
    except Exception as e:
        print(f"Failed to register {m}: {e}")

conn.commit()
conn.close()
print("Recovery completed.")
