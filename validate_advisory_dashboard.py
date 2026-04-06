import os
import uuid
import json
from datetime import datetime
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_advisory_dashboard():
    print("--- VALIDANDO OMNIWEB: GOVERNANCE_ADVISORY_DASHBOARD ---")
    
    with set_chip_context("core"):
        # 1. Setup Scenario: A strong cluster (3+ signals) to generate an advisory
        print("Preparando escenario de deuda transversal (Dashboard Simulation)...")
        b1 = branch_manager.create_branch(name="Dashboard Test Branch")
        sids = [f"dash-ex-{uuid.uuid4().hex[:4]}" for _ in range(3)]
        
        with db_manager.get_connection() as conn:
            for sid in sids:
                conn.execute("""
                    INSERT INTO branch_arbitrations 
                    (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (sid, b1.branch_id, "APPROVE_ANYWAY", "Critical CSS/UI Drift for Dashboard test.", 0.2, "PENDING", datetime.now(), json.dumps(["Fix CSS"])))
            
            # Debug count
            cnt = conn.execute("SELECT count(*) FROM branch_arbitrations WHERE arbitration_id LIKE 'dash-ex-%'").fetchone()[0]
            print(f"DEBUG: Señales 'dash-ex' en DB: {cnt}")
            conn.commit()

        # 2. Extract Dashboard
        print("\nGenerando Cabina de Asesoría (Dashboard Engine)...")
        dashboard = branch_manager.get_governance_advisory_dashboard()
        
        print(f"Total Advisories en Cabina: {len(dashboard)}")
        # Find the advisory that contains our signals
        # We look for the pattern in memory_clusters that has all our sids
        report = branch_manager.get_exceptions_report()
        print(f"Clusters reportados: {len(report.memory_clusters)}")
        for i, p in enumerate(report.memory_clusters):
            print(f" Cluster {i}: {len(p.linked_signal_ids)} señales. Ex: {p.linked_signal_ids[:5]}")
            
        my_p = next((p for p in report.memory_clusters if any(sid in p.linked_signal_ids for sid in sids)), None)
        assert my_p is not None, "Ninguna señal de test se encontró en ningún clúster."
        print(f"Señal(es) de test encontradas en clúster {my_p.pattern_id}")
        
        aid = f"adv_{my_p.pattern_id}"
        my_adv = next((a for a in dashboard if a["advisory_id"] == aid), None)
        assert my_adv is not None, "La nueva advisory debería aparecer en el dashboard."
        print(f"Advisory encontrada: {my_adv['advisory_id']} (State: {my_adv['state']})")
        assert my_adv["state"] == "PENDING", "El estado inicial debería ser PENDING."

        # 3. Accept Advisory and check dashboard again
        print("\nSimulando Aceptación...")
        branch_manager.accept_governance_advisory(aid)
        
        dashboard_v2 = branch_manager.get_governance_advisory_dashboard()
        my_adv_v2 = next((a for a in dashboard_v2 if a["advisory_id"] == aid), None)
        print(f"Advisory ACTUALIZADA encontrada: {my_adv_v2['advisory_id']} (State: {my_adv_v2['state']})")
        assert my_adv_v2["state"] == "ACCEPTED", "El estado debería haber cambiado a ACCEPTED."
        assert my_adv_v2["linked_handoff"] is not None, "Debería estar vinculada a una misión."

        # 4. Simulate Impact (Pattern gone)
        print("\nSimulando Impacto Confirmado (Patrón eliminado)...")
        # In runtime, pattern is gone if signals are archived.
        # But signals are still in DB as PENDING in our test.
        # Let's delete our sids to simulate pattern resolution.
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM branch_arbitrations WHERE arbitration_id IN (?, ?, ?)", (sids[0], sids[1], sids[2]))
            conn.commit()
            
        dashboard_v3 = branch_manager.get_governance_advisory_dashboard()
        my_adv_v3 = next((a for a in dashboard_v3 if a["advisory_id"] == aid), None)
        print(f"Advisory IMPACTO encontrada: {my_adv_v3['advisory_id']} (State: {my_adv_v3['state']})")
        print(f"Reducción Observada: {my_adv_v3['observed_reduction']*100}%")
        assert my_adv_v3["state"] == "IMPACT_CONFIRMED", "El estado debería reflejar impacto confirmado si el patrón desaparece."

        # Cleanup
        branch_manager.delete_branch(b1.branch_id)
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM governance_advisories WHERE advisory_id = ?", (aid,))
            conn.execute("DELETE FROM mission_handoffs WHERE handoff_id = ?", (my_adv_v2["linked_handoff"],))
            conn.commit()
            
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_advisory_dashboard()
