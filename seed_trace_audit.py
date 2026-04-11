
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def seed_trace_deep_linking_data():
    print("Seeding Catalyst Trace Audit Data...")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            node_id = "WNODE-TEST-001"
            trace_id = "CAT-AUDIT-TEST-99"
            
            # 1. Create a Catalyst Trace in Ledger
            events = [
                ("INVOKE", {"objective": "Optimize database queries", "tactic_id": node_id}),
                ("SUCCESS", {"objective": "Optimize database queries", "steps": [{"step": "Add Index", "status": "PENDING"}], "confidence": 0.99})
            ]
            
            for evt_type, data in events:
                conn.execute("""
                    INSERT OR REPLACE INTO governance_decision_ledger (
                        ledger_id, decision_type, target_ref_type, target_id, rationale, evidence_refs, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    f"LEDG-TR-{uuid.uuid4().hex[:8].upper()}",
                    f"CATALYST_{evt_type}",
                    "CATALYST_TRACE",
                    trace_id,
                    f"Catalyst Event: {evt_type}",
                    json.dumps(data),
                    datetime.now().isoformat()
                ))

            # 2. Add an evidence item with this trace_id
            conn.execute("""
                INSERT OR REPLACE INTO governance_post_mission_syncs (
                    sync_id, source_package_id, source_mission_id, source_atlas_node_ids,
                    actual_outcome_type, rationale, creator_decision, is_applied, 
                    proposed_confidence_delta, catalyst_trace_id,
                    project_id, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "SYNC-WITH-TRACE-01", "PKG-001", "MISS-TRACE-01", json.dumps([node_id]),
                "WISDOM_CONFIRMED", "Misión acelerada exitosamente.", "ACCEPTED", 1,
                0.05, trace_id, "PROJECT_OMNIWEB_PROD", datetime.now().isoformat()
            ))
            
            conn.commit()
    print("Seed completed.")

if __name__ == "__main__":
    seed_trace_deep_linking_data()
