import os
import uuid
import json
from datetime import datetime
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_governance_advisory():
    print("--- VALIDANDO OMNIWEB: GOVERNANCE_ADVISORY_LOOP ---")
    
    with set_chip_context("core"):
        # 1. Setup Scenario: A strong cluster (3+ signals)
        print("Preparando escenario de patrón de deuda fuerte (Visual/CSS)...")
        b1 = branch_manager.create_branch(name="Visual Patch A")
        
        # 3 CSS Signals
        sids = [f"css-ex-{uuid.uuid4().hex[:4]}" for _ in range(3)]
        
        with db_manager.get_connection() as conn:
            for sid in sids:
                conn.execute("""
                    INSERT INTO branch_arbitrations 
                    (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (sid, b1.branch_id, "APPROVE_ANYWAY", "Visual CSS drift detected.", 0.2, "PENDING", datetime.now(), json.dumps(["Fix CSS"])))
            conn.commit()

        # 2. Check Report for Advisories
        print("\nVerificando generación de Advisory...")
        report = branch_manager.get_exceptions_report()
        
        print(f"Clusters detectados: {len(report.memory_clusters)}")
        print(f"Advisories generadas: {len(report.advisories)}")
        
        # Robust check: Find advisory linked to the pattern that contains our SIDs
        my_pattern = next((p for p in report.memory_clusters if all(sid in p.linked_signal_ids for sid in sids)), None)
        assert my_pattern is not None, "Debería existir un clúster con las 3 señales."
        
        my_adv = next((a for a in report.advisories if a.source_pattern_id == my_pattern.pattern_id), None)
        assert my_adv is not None, "El clúster de 3 señales debería haber generado una Advisory."
        
        print(f"Advisory Detectada: {my_adv.advisory_type} - {my_adv.proposed_objective}")
        print(f"Rationale: {my_adv.rationale}")

        # 3. Accept Advisory
        print("\nSimulando aceptación de Advisory por el Creador...")
        res = branch_manager.accept_governance_advisory(my_adv.advisory_id)
        if res["status"] != "success":
            print(f"ERROR EN ACEPTACIÓN: {res}")
        assert res["status"] == "success", "La aceptación de la advisory debería ser exitosa."
        mid = res["mission_id"]
        print(f"Misión creada: {mid}")

        # 4. Verify mission in DB
        print("\nVerificando persistencia de la misión estratégica...")
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT briefing_title, source_type FROM mission_handoffs WHERE handoff_id = ?", (mid,)).fetchone()
            assert row is not None, "La misión debería existir en la base de datos."
            print(f"Misión en DB: {row[0]} (Source: {row[1]})")
            assert row[1] == "strategic_governance", "El tipo de origen debería ser 'strategic_governance'."

        # 5. Case B: Weak Cluster (No over-reaction)
        print("\nVerificando caso de patrón débil (sin advisory)...")
        b2 = branch_manager.create_branch(name="Minor Tweak")
        sid_weak = f"weak-ex-{uuid.uuid4().hex[:4]}"
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid_weak, b2.branch_id, "PENDING", "Minor drift.", 0.1, "PENDING", datetime.now(), json.dumps(["Fix"])))
            conn.commit()
            
        report_weak = branch_manager.get_exceptions_report()
        # Find if sid_weak is in any advisory
        sid_weak_adv = next((a for a in report_weak.advisories if sid_weak in a.rationale), None)
        assert sid_weak_adv is None, "Una señal única no debería generar una Advisory estructural."
        print("Gobernanza prudente validada: Patrón débil no escala a Advisory.")

        # Cleanup
        branch_manager.delete_branch(b1.branch_id)
        branch_manager.delete_branch(b2.branch_id)
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM branch_arbitrations WHERE arbitration_id LIKE 'css-ex-%' OR arbitration_id LIKE 'weak-ex-%'")
            conn.execute("DELETE FROM mission_handoffs WHERE handoff_id = ?", (mid,))
            conn.commit()
            
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_governance_advisory()
