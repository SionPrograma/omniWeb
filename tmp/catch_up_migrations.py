import sys
import os
sys.path.append(os.getcwd())
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

# List of migrations that appear to be already applied based on existing tables/columns
to_mark = [
    "098_handoff_ancestry.sql",
    "099_persona_merge_governance.sql",
    "100_compensation_effectiveness.sql",
    "101_granular_effectiveness.sql",
    "102_arbitration_flow.sql",
    "103_exception_tracking.sql"
]

with set_chip_context("core"):
    conn = db_manager.get_connection()
    for m in to_mark:
        try:
            conn.execute("INSERT OR IGNORE INTO system_migrations (filename) VALUES (?)", (m,))
            print(f"Marked {m} as applied.")
        except Exception as e:
            print(f"Failed to mark {m}: {e}")
    conn.commit()
