import os
import uuid
import json
from datetime import datetime, timedelta
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_recurrence_protector():
    print("--- VALIDANDO OMNIWEB: CONSTITUTIONAL_RECURRENCE_PROTECTOR ---")
    
    with set_chip_context("core"):
        # 1. Setup Scenario: A Recurrent Signal (3 recoveries)
        print("Preparando escenario de recurrencia crítica (3 recoveries)...")
        b = branch_manager.create_branch(name="Recurrence Test Branch")
        sid = f"recur-{uuid.uuid4().hex[:6]}"
        
        t_base = datetime.now() - timedelta(days=20)
        
        with db_manager.get_connection() as conn:
            # Creation (Use PENDING to be visible in report active list)
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid, b.branch_id, "APPROVE_WITH_CONDITIONS", "Drift persistente detectado.", 0.5, "PENDING", t_base, "[]"))
            
            # 3 Recovery Missions (This triggers STRUCTURAL_REVIEW)
            for i in range(3):
                mid = f"mission-{sid}-{i}"
                conn.execute("""
                    INSERT INTO mission_handoffs (handoff_id, briefing_title, readiness_state, created_at, objective)
                    VALUES (?, ?, ?, ?, ?)
                """, (mid, f"SANEAMIENTO: {sid} - Intento {i}", "COMPLETED", t_base + timedelta(days=i*2), "Fix it."))
            
            conn.commit()

        # 2. Analyze Recurrence
        print("\nAnalizando recurrencia...")
        risk = branch_manager.analyze_recurrence(sid)
        print(f"Estado de Recurrencia: {risk.recurrence_state}")
        print(f"Permiso de Archivado: {risk.archive_permission}")
        print(f"Riesgo Estructural: {risk.structural_risk_score}")
        print(f"Acción Sugerida: {risk.next_required_action}")
        
        assert risk.recurrence_state == "CRITICAL", f"Debería ser CRITICAL, se obtuvo: {risk.recurrence_state}"
        assert not risk.archive_permission, "El archivado debería estar BLOQUEADO."
        assert risk.next_required_action == "STRUCTURAL_REVIEW", "Debería sugerir revisión estructural."

        # 3. Pruning Integration Check
        print("\nVerificando candidatos de pruning...")
        candidates = branch_manager.get_pruning_candidates()
        target = next((c for c in candidates if c.signal_id == sid), None)
        
        if target:
            print(f"Candidato detectado: {target.candidate_type}")
            print(f"Bloqueo Activo: {not target.archive_permission}")
            assert target.candidate_type == "RECURRENT_GATED", "Tipo de candidato debería ser RECURRENT_GATED."
            assert not target.archive_permission, "No debería tener permiso de archivado."
        else:
            print("ERROR: La señal no apareció como candidata a pesar de su antigüedad y bajo impacto.")
            # Let's inspect why
            report = branch_manager.get_exceptions_report()
            found = [ex for ex in report.active_exceptions if ex.exception_id == sid]
            if not found: print(f" - Señal no encontrada en reporte activo. Estado: {sid}")
            else: print(f" - Señal encontrada en reporte. Triage: {found[0].triage.classification}")

        # 4. Forensics Replay Check
        print("\nVerificando Replay Forense...")
        replay = branch_manager.get_forensics_replay(sid)
        print(f"Trayectoria Forense: {replay.trajectory}")
        assert replay.trajectory == "STRUCTURAL_REVIEW", "Trayectoria incorrecta en Replay."

        # Cleanup
        branch_manager.delete_branch(b.branch_id)
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM branch_arbitrations WHERE arbitration_id = ?", (sid,))
            conn.execute("DELETE FROM mission_handoffs WHERE briefing_title LIKE ?", (f"%{sid}%",))
            conn.commit()
            
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_recurrence_protector()
