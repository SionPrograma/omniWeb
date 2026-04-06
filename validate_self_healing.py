import os
import json
import uuid
from backend.core.ai_host.memory.branch_manager import branch_manager, HealingPackage, HealingAction
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_self_healing():
    print("--- VALIDANDO OMNIWEB: CONSTITUTIONAL_SELF_HEALING_PREVIEW ---")
    
    with set_chip_context("core"):
        # 1. Create a set of LOW_IMPACT exceptions
        print("Creando señales de bajo impacto...")
        b1 = branch_manager.create_branch(name="Minor CSS Tweak")
        branch_manager.apply_arbitration_decision(
            b1.branch_id, 
            decision="APPROVE_WITH_CONDITIONS", 
            rationale="Ajuste visual menor.", 
            conditions=["Fix CSS"]
        )
        
        b2 = branch_manager.create_branch(name="Minor Layout Tweak")
        branch_manager.apply_arbitration_decision(
            b2.branch_id, 
            decision="APPROVE_WITH_CONDITIONS", 
            rationale="Ajuste de padding.", 
            conditions=["Ajustar Visual padding"]
        )
        
        # Ensure they are classified as LOW_IMPACT or SIGNAL_NOISE
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE branch_arbitrations SET debt_level = 0.4")
            conn.commit()

        # 2. Test Grouping Engine
        print("\nGenerando propuestas de Self-Healing...")
        packages = branch_manager.generate_healing_packages()
        
        print(f"Paquetes generados: {len(packages)}")
        for p in packages:
            print(f" - PAQUETE: {p.name}. Señales: {len(p.signals)}. Acciones: {len(p.proposed_actions)}")
        
        assert len(packages) > 0
        pkg = packages[0]
        assert "UI_CLEANUP_BATCH" in pkg.name or "GENERAL_TUNING_BATCH" in pkg.name
        
        # 3. Test Partial Acceptance
        print("\nAceptando parcialmente el paquete...")
        action_ids = [pkg.proposed_actions[0].action_id]
        res = branch_manager.apply_healing_actions(action_ids, pkg)
        
        print(f"Resultado de aplicación: {res}")
        assert res["injected_actions"] == 1
        
        # 4. Verify Traceability
        print("\nVerificando trazabilidad en DB...")
        with db_manager.get_connection() as conn:
            # Check if handoff was created
            handoff = conn.execute("SELECT * FROM mission_handoffs WHERE briefing_title LIKE 'HEALING:%'").fetchone()
            print(f"Handoff de Healing encontrado: {handoff['briefing_title'] if handoff else 'NOT FOUND'}")
            assert handoff is not None
            
            # Check if signals are marked as PLANNING
            for sid in pkg.signals:
                state = conn.execute("SELECT compliance_state FROM branch_arbitrations WHERE arbitration_id = ?", (sid,)).fetchone()
                print(f"Señal {sid} estado: {state[0]}")
                assert state[0] == "PLANNING"

        # Cleanup
        branch_manager.delete_branch(b1.branch_id)
        branch_manager.delete_branch(b2.branch_id)
        
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_self_healing()
