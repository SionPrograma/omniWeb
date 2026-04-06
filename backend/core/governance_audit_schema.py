import sqlite3
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def apply_root_audit_schema():
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS governance_root_audit_proposals (
                    audit_id TEXT PRIMARY KEY,
                    source_heatmap_node TEXT NOT NULL,
                    source_relief_ids TEXT, 
                    trigger_state TEXT NOT NULL, 
                    confidence REAL,
                    structural_resistance_score REAL,
                    repeated_failure_count INTEGER DEFAULT 0,
                    proposed_objective TEXT,
                    proposed_scope TEXT,
                    rationale TEXT,
                    status TEXT DEFAULT 'PENDING',
                    associated_handoff_id TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            print("Escalado: Tabla governance_root_audit_proposals creada.")

if __name__ == "__main__":
    apply_root_audit_schema()
