import sqlite3
from backend.core.database import db_manager

def apply_autopsy_schema():
    print("OMNIWEB — BLOQUE: FORENSIC BRANCH AUTOPSY SCHEMA.")
    with db_manager.get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS governance_branch_autopsies (
            autopsy_id TEXT PRIMARY KEY,
            branch_id TEXT NOT NULL,
            branch_goal_summary TEXT,
            affected_domains TEXT,
            hotspot_history TEXT,
            advisories_generated TEXT,
            creator_actions_summary TEXT,
            debt_events TEXT,
            resistance_events TEXT,
            root_audit_events TEXT,
            final_branch_outcome TEXT,
            lessons_learned TEXT,
            structural_findings TEXT,
            recommended_followup TEXT,
            confidence REAL,
            created_at TIMESTAMP,
            FOREIGN KEY(branch_id) REFERENCES roadmap_branches(branch_id)
        )
        """)
        conn.commit()
    print("Schema applied successfully.")

if __name__ == "__main__":
    apply_autopsy_schema()
