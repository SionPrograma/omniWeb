import os
import json
import uuid
from datetime import datetime, timedelta
from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

def validate_forensics_replay():
    print("--- VALIDANDO OMNIWEB: GOVERNANCE_DRIFT_FORENSICS_REPLAY ---")
    
    with set_chip_context("core"):
        # 1. Setup a complex scenario: Creation -> Recovery -> Archive
        print("Preparando escenario forense...")
        b = branch_manager.create_branch(name="Replay Test Branch")
        sid = f"forensic-{uuid.uuid4().hex[:6]}"
        
        t0 = (datetime.now() - timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S')
        t1 = (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S')
        
        with db_manager.get_connection() as conn:
            # Creation
            conn.execute("""
                INSERT INTO branch_arbitrations 
                (arbitration_id, branch_id, decision, rationale, debt_level, compliance_state, created_at, conditions)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (sid, b.branch_id, "APPROVE_WITH_CONDITIONS", "Drift inicial detectado.", 0.6, "PENDING", t0, "[]"))
            
            # Simulated Recovery Mission (title matches sid)
            # Use handoff_id and readiness_state
            mid = f"mission-{sid}"
            conn.execute("""
                INSERT INTO mission_handoffs (handoff_id, briefing_title, readiness_state, created_at, objective)
                VALUES (?, ?, ?, ?, ?)
            """, (mid, f"SANAR: {sid} - Core Refactor", "COMPLETED", t1, "Sanar deuda tecnica."))
            
            conn.commit()

        # Archive it
        print("Archivando señal...")
        branch_manager.archive_signals([sid])

        # 2. Replay Reconstruction
        print("\nReconstruyendo Replay Forense...")
        replay = branch_manager.get_forensics_replay(sid)
        
        print(f"Trayectoria detectada: {replay.trajectory}")
        print(f"Resumen: {replay.summary}")
        print(f"Eventos encontrados: {len(replay.events)}")
        
        found_created = False
        found_recovery = False
        found_archived = False
        
        for ev in replay.events:
            print(f" - [{ev.timestamp}] {ev.event_type}: {ev.title}")
            if ev.event_type == "CREATED": found_created = True
            if ev.event_type == "RECOVERY": found_recovery = True
            if ev.event_type == "ARCHIVED": found_archived = True
            
        assert found_created, "Evento CREATED no encontrado."
        assert found_recovery, "Evento RECOVERY no encontrado."
        assert found_archived, "Evento ARCHIVED no encontrado."
        assert replay.trajectory == "ARCHIVED", f"Trayectoria incorrecta: {replay.trajectory}"

        # Cleanup
        branch_manager.delete_branch(b.branch_id)
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM branch_arbitrations WHERE arbitration_id = ?", (sid,))
            conn.execute("DELETE FROM mission_handoffs WHERE handoff_id = ?", (mid,))
            conn.commit()
            
        print("\nDONE: VALIDACIÓN COMPLETADA.")

if __name__ == "__main__":
    validate_forensics_replay()
