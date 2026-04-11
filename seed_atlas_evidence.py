
import json
import sqlite3
import uuid
from datetime import datetime, timedelta
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def seed_evidence_data():
    print("Seeding Atlas Evidence Data...")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 1. Ensure target node exists (or create one)
            node_id = "WNODE-TEST-001"
            conn.execute("""
                INSERT OR REPLACE INTO governance_wisdom_atlas_nodes (
                    node_id, node_type, title, summary, confidence, reusability_score, status_band, 
                    affected_domains, related_refs, evidence_refs
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                node_id, "LEARNING", "Test Wisdom Node", 
                "Esta es una unidad de sabiduría de prueba para validar la UI de evidencia.",
                0.75, 0.8, "EXPERIMENTAL", 
                json.dumps(["core"]), json.dumps([]), json.dumps({"test_meta": "valid"})
            ))

            # 2. Add some sync history
            outcomes = [
                ("WISDOM_CONFIRMED", "Misión exitosa, validando el patrón técnico.", "ACCEPTED", 1),
                ("WISDOM_PARTIAL", "Éxito parcial con fricción moderada.", "ACCEPTED", 1),
                ("WISDOM_CONTRADICTED", "Fallo detectado a pesar de seguir el draft.", "ACCEPTED", 1),
                ("EXECUTION_BIASED", "Precondiciones ignoradas por el equipo.", "ACCEPTED", 1),
                ("WISDOM_CONFIRMED", "Nueva validación pendiente de revisión.", "PENDING", 0)
            ]

            for i, (outcome, rationale, decision, applied) in enumerate(outcomes):
                sync_id = f"SYNC-TEST-{i}"
                created_at = (datetime.now() - timedelta(days=i)).isoformat()
                conn.execute("""
                    INSERT OR REPLACE INTO governance_post_mission_syncs (
                        sync_id, source_package_id, source_mission_id, source_atlas_node_ids,
                        actual_outcome_type, rationale, creator_decision, is_applied, 
                        proposed_confidence_delta, proposed_reusability_delta,
                        project_id, supporting_evidence, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    sync_id, "PKG-001", f"MISS-{i}", json.dumps([node_id]),
                    outcome, rationale, decision, applied,
                    0.05 if "CONFIRMED" in outcome else -0.1 if "CONTRADICTED" in outcome else 0.0,
                    0.02, "PROJECT_OMNIWEB_PROD", json.dumps({"test": True}), created_at
                ))
            
            conn.commit()
    print("Seed completed.")

if __name__ == "__main__":
    seed_evidence_data()
