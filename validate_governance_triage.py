import os
import json
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_governance_triage():
    print("--- VALIDANDO OMNIWEB: GOVERNANCE_NOISE_CLASSIFICATION ---")
    
    with set_chip_context("core"):
        # 1. Setup a CRITICAL Exception
        b1 = branch_manager.create_branch(name="Rama de Alto Riesgo")
        branch_manager.apply_arbitration_decision(
            b1.branch_id,
            decision="APPROVE_ANYWAY",
            rationale="Override crítico estructural.",
            conditions=["Hardening masivo"]
        )
        # Force high debt to trigger CRITICAL (threshold 6.0)
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE branch_arbitrations SET debt_level = 5.0 WHERE branch_id = ?", (b1.branch_id,))
            conn.commit()
        print("Excepción CRÍTICA creada.")

        # 2. Setup a LOW IMPACT Exception
        b2 = branch_manager.create_branch(name="Rama de Cambio Técnico Menor")
        branch_manager.apply_arbitration_decision(
            b2.branch_id,
            decision="APPROVE_WITH_CONDITIONS",
            rationale="Ajuste menor de logs.",
            conditions=["Logs corregidos"]
        )
        # Force low debt
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE branch_arbitrations SET debt_level = 0.5 WHERE branch_id = ?", (b2.branch_id,))
            conn.commit()
        print("Excepción de BAJO IMPACTO creada.")

        # 3. Trigger Triage Result
        print("\nEjecutando Triage en Reporte Forense...")
        report = branch_manager.get_exceptions_report()
        
        print(f"Total Excepciones Activas: {len(report.active_exceptions)}")
        
        critical = [ex for ex in report.active_exceptions if ex.triage.classification == "CRITICAL_DEBT"]
        low = [ex for ex in report.active_exceptions if ex.triage.classification == "SIGNAL_NOISE" or ex.triage.classification == "LOW_IMPACT"]
        
        print(f"Detectadas {len(critical)} Críticas y {len(low)} de Bajo Impacto.")
        
        assert len(critical) > 0
        assert len(low) > 0
        
        # Verify Rationale
        print(f"Rationale Triage Crítica: {critical[0].triage.rationale}")
        print(f"Rationale Triage Baja: {low[0].triage.rationale}")

        # Cleanup
        branch_manager.delete_branch(b1.branch_id)
        branch_manager.delete_branch(b2.branch_id)
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_governance_triage()
