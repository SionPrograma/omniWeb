import os
import json
import uuid
from datetime import datetime, timedelta
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_auto_pruning():
    print("--- VALIDANDO OMNIWEB: GOVERNANCE_AUTO_PRUNING_PREVIEW ---")
    
    with set_chip_context("core"):
        # Unique IDs for this run
        sid_stable = f"stable-{uuid.uuid4().hex[:6]}"
        sid_active = f"active-{uuid.uuid4().hex[:6]}"
        
        # 1. Create Branches for the signals
        print(f"Creando ramas y señales ({sid_stable}, {sid_active})...")
        b_stable = branch_manager.create_branch(name=f"Old Fix {sid_stable}")
        b_active = branch_manager.create_branch(name=f"Recent Fix {sid_active}")
        
        old_date = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        now_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid_stable, b_stable.branch_id, "APPROVE_WITH_CONDITIONS", "Minor noise.", 0.3, "PENDING", old_date, "[]"))
            
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid_active, b_active.branch_id, "APPROVE_WITH_CONDITIONS", "Active noise.", 0.5, "PENDING", now_date, "[]"))
            
            conn.commit()

        # 2. Test Pruning Engine
        print("\nIdentificando candidatos a archivado...")
        candidates = branch_manager.get_pruning_candidates()
        
        print(f"Candidatos encontrados: {len(candidates)}")
        found_stable = False
        found_active_in_pruning = False
        
        for c in candidates:
            if c.signal_id == sid_stable:
                print(f" - CANDIDATO detectado: {c.signal_id} (Type: {c.candidate_type}, Stability: {c.stability_score})")
                found_stable = True
            if c.signal_id == sid_active:
                found_active_in_pruning = True
            
        assert found_stable, f"La señal vieja {sid_stable} debería ser candidata."
        assert not found_active_in_pruning, f"La señal reciente {sid_active} NO debería ser candidata."
        
        # 3. Test Archival Application
        print(f"\nAplicando archivado a la señal {sid_stable}...")
        res = branch_manager.archive_signals([sid_stable])
        
        print(f"Resultado de archivado: {res}")
        assert res["archived_count"] == 1
        
        # 4. Verify in Report
        print("\nVerificando visibilidad en el reporte...")
        report = branch_manager.get_exceptions_report()
        
        is_in_resolved = any(ex.exception_id == sid_stable for ex in report.resolved_exceptions)
        is_in_active = any(ex.exception_id == sid_stable for ex in report.active_exceptions)
        
        print(f"Señal en resueltos: {is_in_resolved}")
        print(f"Señal en activos: {is_in_active}")
        
        assert is_in_resolved, "La señal archivada debe estar en la lista de resueltos."
        assert not is_in_active, "La señal archivada no debe estar en activos."

        # Cleanup
        branch_manager.delete_branch(b_stable.branch_id)
        branch_manager.delete_branch(b_active.branch_id)
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM branch_arbitrations WHERE arbitration_id IN (?, ?)", (sid_stable, sid_active))
            conn.commit()
            
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_auto_pruning()
