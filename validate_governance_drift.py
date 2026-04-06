import os
import json
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_governance_drift():
    print("--- VALIDANDO OMNIWEB: GOVERNANCE_DRIFT_RADAR ---")
    
    with set_chip_context("core"):
        # 1. Setup an Active Exception (Debt)
        b_old = branch_manager.create_branch(name="Rama Antigua con Deuda CSS")
        branch_manager.apply_arbitration_decision(
            b_old.branch_id,
            decision="APPROVE_WITH_CONDITIONS",
            rationale="Override visual para demo.",
            conditions=["Sanar CSS del dashboard"]
        )
        print("Deuda constitucional activa creada.")

        # 2. Create a NEW branch that relapses into the same domain
        b_new = branch_manager.create_branch(name="Nueva Rama con Drift")
        
        # Inject high friction in DESIGNER role to trigger DOMAIN_RELAPSE
        summary = {
            "friction": 0.8,
            "readiness": 0.2
        }
        verdict = {
            "persona_details": {
                "DESIGNER": {"friction": 0.9, "rationale": "Nuevos cambios visuales agresivos."},
                "ARCHITECT": {"friction": 0.1}
            }
        }
        
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE roadmap_branches 
                SET simulation_summary = ?, persona_verdict = ?, constitutional_status = 'WARNING'
                WHERE branch_id = ?
            """, (json.dumps(summary), json.dumps(verdict), b_new.branch_id))
            conn.commit()
            
        print(f"Branch {b_new.branch_id} preparada con alta fricción en diseño.")

        # 3. Trigger Drift Detection
        print("\nEjecutando Radar de Deriva...")
        alerts = branch_manager.detect_governance_drift(b_new.branch_id)
        
        print(f"Alertas detectadas: {len(alerts)}")
        assert len(alerts) > 0
        
        relapse = next((a for a in alerts if a.drift_type == "DOMAIN_RELAPSE"), None)
        assert relapse is not None
        print(f"ALERTA: {relapse.drift_type} (Severidad: {relapse.severity})")
        print(f"Rationale: {relapse.rationale}")
        print(f"Acción Sugerida: {relapse.suggested_action}")

        # 4. Verify presence in Strategic Dashboard
        print("\nVerificando integración en Dashboard Estratégico...")
        dashboard = branch_manager.get_strategic_dashboard()
        target = next((b for b in dashboard.active_branches if b.branch_id == b_new.branch_id), None)
        
        assert target is not None
        assert len(target.drift_alerts) > 0
        print(f"Dashboard confirma {len(target.drift_alerts)} alertas para la rama con drift.")

        # Cleanup
        branch_manager.delete_branch(b_old.branch_id)
        branch_manager.delete_branch(b_new.branch_id)
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_governance_drift()
