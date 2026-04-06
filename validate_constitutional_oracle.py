import os
import json
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_constitutional_oracle():
    print("--- VALIDANDO OMNIWEB: CONSTITUTIONAL_HEALTH_ORACLE ---")
    
    with set_chip_context("core"):
        # 1. Setup an Active Exception
        b = branch_manager.create_branch(name="Rama con Deuda Sistémica")
        arb = branch_manager.apply_arbitration_decision(
            b.branch_id,
            decision="APPROVE_ANYWAY",
            rationale="Override estructural para cumplir deadline.",
            conditions=["Hardening masivo de Core"]
        )
        eid = arb.arbitration_id
        print(f"Excepción {eid} creada.")

        # 2. Test Oracle Projection for Exception
        print("\nConsultando Oráculo (Escenarios de Deuda)...")
        forecasts = branch_manager.project_constitutional_health(eid, type="exception")
        
        print(f"Escenarios proyectados: {len(forecasts)}")
        assert len(forecasts) >= 2
        
        do_nothing = next((f for f in forecasts if f.scenario == "DO_NOTHING"), None)
        sanar = next((f for f in forecasts if f.scenario == "SANAR_AHORA"), None)
        
        assert do_nothing is not None
        assert sanar is not None
        print(f"Escenario DO_NOTHING: Deuda Proyectada {do_nothing.debt_score} (Conf: {do_nothing.confidence})")
        print(f"Escenario SANAR_AHORA: Deuda Proyectada {sanar.debt_score} (Conf: {sanar.confidence})")
        assert do_nothing.debt_score > sanar.debt_score

        # 3. Test Oracle for Branch with Drift
        print("\nConsultando Oráculo para Rama con Drift...")
        # (Using the same logic as drift radar to trigger Scenario 3)
        b_drift = branch_manager.create_branch(name="Rama Relapse")
        verdict = {"persona_details": {"ARCHITECT": {"friction": 0.9}}} # Friction in ARCHITECT domain
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE roadmap_branches SET persona_verdict = ?, constitutional_status = 'WARNING' WHERE branch_id = ?", 
                         (json.dumps(verdict), b_drift.branch_id))
            conn.commit()
            
        forecasts_drift = branch_manager.project_constitutional_health(b_drift.branch_id, type="branch")
        drift_scenario = next((f for f in forecasts_drift if f.scenario == "ACEPTAR_DERIVA"), None)
        
        assert drift_scenario is not None
        print(f"Escenario ACEPTAR_DERIVA: Fragilidad {drift_scenario.domain_fragility}")
        print(f"Rationale: {drift_scenario.rationale}")

        # Cleanup
        branch_manager.delete_branch(b.branch_id)
        branch_manager.delete_branch(b_drift.branch_id)
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_constitutional_oracle()
