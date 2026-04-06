import os
import json
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_recovery_preview():
    print("--- VALIDANDO OMNIWEB: GOVERNANCE_RECOVERY_PREVIEW ---")
    
    with set_chip_context("core"):
        # 1. Setup an Exception (Arbitrated branch with conditions)
        b = branch_manager.create_branch(name="Rama con Deuda de Seguridad")
        bid = b.branch_id
        
        # Apply arbitration with specific keywords to trigger the engine
        arb = branch_manager.apply_arbitration_decision(
            bid,
            decision="APPROVE_WITH_CONDITIONS",
            rationale="Necesito override para demo, pero hay que arreglar auth.",
            conditions=["Hardening de AUTH y perfiles", "Revisar CSS de botones"]
        )
        eid = arb.arbitration_id
        print(f"Excepción {eid} creada para {bid}.")

        # 2. Test Recovery Proposal Generation
        print("\nGenerando Propuestas de Recovery...")
        proposals = branch_manager.generate_recovery_proposals(eid)
        
        print(f"Propuestas generadas: {len(proposals)}")
        assert len(proposals) >= 2
        
        auth_prop = next((p for p in proposals if p.proposed_mission_type == "GOVERNANCE_RECOVERY"), None)
        css_prop = next((p for p in proposals if p.proposed_mission_type == "DESIGN_ALIGNMENT_RECOVERY"), None)
        
        assert auth_prop is not None
        assert css_prop is not None
        print(f"Propuesta 1: {auth_prop.suggested_objective} (Domain: {auth_prop.target_domain})")
        print(f"Propuesta 2: {css_prop.suggested_objective} (Domain: {css_prop.target_domain})")

        # 3. Test Injection (Accepting the first proposal)
        print("\nInyectando Propuesta de Recovery...")
        res = branch_manager.apply_recovery_proposal(auth_prop)
        
        print(f"Status inyección: {res['status']}")
        print(f"Mission ID en backlog: {res['mission_id']}")
        print(f"Estado de cumplimiento: {res['state']}")
        
        # 4. Verify Exception State
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT compliance_state FROM branch_arbitrations WHERE arbitration_id = ?", (eid,)).fetchone()
            print(f"Estado en DB: {row['compliance_state']}")
            assert row['compliance_state'] == "PLANNING"
            
            # Verify mission in handoffs
            h = conn.execute("SELECT * FROM mission_handoffs WHERE handoff_id = ?", (res['mission_id'],)).fetchone()
            print(f"Misión en Backlog: {h['briefing_title']} - {h['objective']}")
            assert h['source_type'] == "system_governance"

        # Cleanup
        branch_manager.delete_branch(bid)
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_recovery_preview()
