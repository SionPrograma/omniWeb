import os
import json
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_arbitration_flow():
    print("--- VALIDANDO OMNIWEB: CREATOR_CORE_ARBITRATION_FLOW ---")
    
    with set_chip_context("core"):
        # 1. Setup an Escalated branch
        b = branch_manager.create_branch(name="Rama para Arbitraje")
        bid = b.branch_id
        
        # Mock high friction and ESCALATE state
        with db_manager.get_connection() as conn:
            verdict = {
                "state": "BLOCKED_BY_PERSONA_TENSION",
                "persona_details": {
                    "DESIGNER": {"friction": 0.85, "support": 0.15},
                    "ARCHITECT": {"friction": 0.2, "support": 0.8}
                }
            }
            conn.execute("""
                UPDATE roadmap_branches 
                SET persona_verdict = ?, constitutional_status = 'WARNING', divergence_score = 0.5 
                WHERE branch_id = ?
            """, (json.dumps(verdict), bid))
            conn.commit()
            
        print(f"Branch {bid} escalada.")

        # 2. Test Dossier Generation
        print("\nGenerando Dossier...")
        dossier = branch_manager.get_branch_dossier(bid)
        print(f"Dossier para {dossier.branch.name} obtenido.")
        assert dossier.persona_friction_map["DESIGNER"] == 0.85

        # 3. Test Arbitration Decision: APPROVE_ANYWAY
        print("\nAplicando Decisión: APPROVE_ANYWAY (Override)")
        arb = branch_manager.apply_arbitration_decision(
            bid, 
            decision="APPROVE_ANYWAY", 
            rationale="Necesidad estratégica crítica por encima de fricción de diseño.",
            conditions=["Hardening visual en siguiente fase"]
        )
        print(f"Arbitraje ID: {arb.arbitration_id}")
        
        # Verify branch state changed
        b_after = branch_manager.get_branch(bid)
        print(f"Nuevo estado: {b_after.branch_state}")
        assert b_after.branch_state == "READY_FOR_MERGE"
        assert b_after.is_arbitrated == 1

        # 4. Verify Traceability
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM branch_arbitrations WHERE arbitration_id = ?", (arb.arbitration_id,)).fetchone()
            print(f"Registro en DB: [{row['decision']}] {row['rationale']}")
            assert row['decision'] == "APPROVE_ANYWAY"
            
            trace = conn.execute("SELECT * FROM persona_merge_audits WHERE branch_id = ? ORDER BY created_at DESC", (bid,)).fetchone()
            print(f"Traza Forense: {trace['rationale']}")

        # 5. Test Veto (on a fresh branch)
        b2 = branch_manager.create_branch(name="Rama para Veto")
        bid2 = b2.branch_id
        print(f"\nAplicando Veto a {bid2}...")
        branch_manager.apply_arbitration_decision(
            bid2, "REJECT_VETO", "Riesgo constitucional inaceptable."
        )
        b2_after = branch_manager.get_branch(bid2)
        print(f"Estado Veto: {b2_after.branch_state}")
        assert b2_after.branch_state == "DISCARDED"

        # Cleanup
        branch_manager.delete_branch(bid)
        branch_manager.delete_branch(bid2)
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_arbitration_flow()
