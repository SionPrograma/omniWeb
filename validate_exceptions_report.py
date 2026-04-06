import os
import json
from datetime import datetime
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_exceptions_report():
    print("--- VALIDANDO OMNIWEB: CONSTITUTIONAL_EXCEPTIONS_REPORT ---")
    
    with set_chip_context("core"):
        # 1. Setup an Arbitrated branch with conditions
        b = branch_manager.create_branch(name="Rama con Deuda Tactica")
        bid = b.branch_id
        
        print(f"Branch {bid} creada.")
        
        # Apply arbitration
        arb = branch_manager.apply_arbitration_decision(
            bid,
            decision="APPROVE_WITH_CONDITIONS",
            rationale="Aprobar para lanzamiento urgente, sanar en Sprint 4.",
            conditions=["Hardening de Auth", "Refactor de CSS"]
        )
        print(f"Arbitraje ID: {arb.arbitration_id} aplicado.")

        # 2. Test Report Generation
        print("\nGenerando Reporte de Excepciones...")
        report = branch_manager.get_exceptions_report()
        
        print(f"Reporte generado. Debt Score: {report.total_debt_score}")
        assert report.total_debt_score >= 1.0
        
        found = next((ex for ex in report.active_exceptions if ex.branch_id == bid), None)
        assert found is not None
        print(f"Excepción activa encontrada para branch: {found.branch_name}")
        print(f"Condiciones detectadas: {found.conditions}")

        # 3. Test Resolution
        print("\nResolviendo Excepción...")
        res = branch_manager.resolve_exception(arb.arbitration_id)
        print(f"Status resolution: {res['status']}")
        
        # 4. Verify in Report again
        report_after = branch_manager.get_exceptions_report()
        print(f"Nuevo Debt Score: {report_after.total_debt_score}")
        
        found_in_active = next((ex for ex in report_after.active_exceptions if ex.branch_id == bid), None)
        found_in_resolved = next((ex for ex in report_after.resolved_exceptions if ex.branch_id == bid), None)
        
        assert found_in_active is None
        assert found_in_resolved is not None
        print(f"Excepción movida a historial: {found_in_resolved.compliance_state}")
        print(f"Fecha resolución: {found_in_resolved.resolved_at}")

        # Cleanup
        branch_manager.delete_branch(bid)
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_exceptions_report()
