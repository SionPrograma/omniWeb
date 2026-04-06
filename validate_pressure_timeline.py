import sys
import os
import uuid
import json
from datetime import datetime

# Mocking essentials to avoid path issues in a standalone script
sys.path.append(os.getcwd())

from backend.core.ai_host.memory.branch_manager import branch_manager, GovernancePressureEvent
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

def validate_pressure_timeline():
    test_handoff_id = f"test_mission_{uuid.uuid4().hex[:8]}"
    test_advisory_id = "ADV-TEST-001"
    
    print(f"--- VALIDATING PRESSURE TIMELINE FOR {test_handoff_id} ---")
    
    with set_chip_context("core"):
        # 1. Simulate Detection
        print("Step 1: Recording PRESSURE_DETECTED...")
        branch_manager._record_pressure_event(GovernancePressureEvent(
            target_id=test_handoff_id,
            event_type="PRESSURE_DETECTED",
            source_advisory_id=test_advisory_id,
            risk_level="HIGH",
            rationale="Prueba de detección de riesgo estructural."
        ))
        
        # 2. Simulate Ignore Decision
        print("Step 2: Recording PRESSURE_IGNORED...")
        branch_manager._record_pressure_event(GovernancePressureEvent(
            target_id=test_handoff_id,
            event_type="PRESSURE_IGNORED",
            source_advisory_id=test_advisory_id,
            risk_level="HIGH",
            creator_decision="IGNORED",
            rationale="El creador decidió ignorar la alerta por prioridad táctica."
        ))
        
        # 3. Simulate Escalation
        print("Step 3: Recording PRESSURE_ESCALATED (Simulated via next detection)...")
        branch_manager._record_pressure_event(GovernancePressureEvent(
            target_id=test_handoff_id,
            event_type="PRESSURE_ESCALATED",
            source_advisory_id=test_advisory_id,
            risk_level="CRITICAL",
            rationale="El riesgo ha escalado a crítico tras cambios en el kernel."
        ))
        
        # 4. Fetch Timeline and Interpret
        print("Step 4: Fetching and Interpreting Timeline...")
        timeline = branch_manager.get_pressure_timeline(test_handoff_id)
        
        print(f"Trajectory Detected: {timeline.trajectory}")
        print(f"Events Count: {len(timeline.events)}")
        print(f"Summary: {timeline.summary}")
        
        # Verification
        assert len(timeline.events) == 3, "Debería haber 3 eventos."
        assert timeline.trajectory in ["IGNORED_AND_DEGRADED", "ESCALATING_PRESSURE"], f"Trayectoria inesperada: {timeline.trajectory}"
        
        # 5. Simulate Recovery
        print("Step 5: Recording REBASE_ACCEPTED...")
        branch_manager._record_pressure_event(GovernancePressureEvent(
            target_id=test_handoff_id,
            event_type="REBASE_ACCEPTED",
            source_advisory_id=test_advisory_id,
            risk_level="LOW",
            creator_decision="ACCEPTED",
            rationale="Rebase aplicado. Misión alineada."
        ))
        
        timeline_final = branch_manager.get_pressure_timeline(test_handoff_id)
        print(f"Final Trajectory: {timeline_final.trajectory}")
        assert timeline_final.trajectory == "REVIEWED_AND_STABILIZED"
    
    print("✅ PRESSURE TIMELINE VALIDATED SUCCESSFULLY (BACKEND).")

if __name__ == "__main__":
    validate_pressure_timeline()
