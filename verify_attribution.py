import sys
import os
import json
from datetime import datetime

# Mock backend environment
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_telemetry import mission_telemetry
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.memory.resource_lock_manager import resource_lock_manager
from backend.core.ai_host.shadow_swarm.approval_gate import approval_gate, GateStatus

def test_attribution():
    # Ensure DB is migrated
    print("Applying migrations...")
    db_manager.run_migrations()
    
    # Create a real mission to satisfy FK constraints
    mission = mission_manager.create_mission("Prueba de Atribución Governance")
    test_id = mission.mission_id
    
    print(f"--- TESTING TELEMETRY ATTRIBUTION [{test_id}] ---")
    
    # 1. Test Mission Manager attribution
    print("Recording MissionManager event...")
    mission_telemetry.record_event(test_id, "test_init", "Iniciando prueba de atribución", source_actor="MissionManager")
    
    # 2. Test ResourceLockManager attribution
    print("Recording ResourceLockManager event...")
    # Simulate a lock acquisition which now triggers telemetry
    resource_lock_manager.acquire_lock("test_resource", test_id, reason="Attribution Test")
    
    # 3. Test ApprovalGate attribution
    print("Recording ApprovalGate event...")
    # Simulate a gate decision
    decision = approval_gate.execute_governance_check(
        intent="Mutación de prueba",
        targets=["backend/core/engine.py"],
        action_type="mutation",
        risk_hint="HIGH",
        proposal_id="test_prop_001",
        active_mission=mission
    )
    
    # 4. Verify in Database
    print("\nVerificando registros en DB...")
    events = mission_telemetry.get_recent_events(test_id, limit=5)
    global_pulse = mission_telemetry.get_portfolio_pulse(limit=10)
    
    print(f"Events for {test_id}:")
    for e in events:
        print(f"  [{e.source_actor}] {e.event_type}: {e.message}")
        if e.source_actor == 'system' and e.event_type != 'test_init':
             print(f"  FAILED: Missing attribution for {e.event_type}")

    print("\nGlobal Pulse (Recent):")
    for e in global_pulse[:3]:
        print(f"  [{e.source_actor}] {e.event_type}: {e.message}")

if __name__ == "__main__":
    try:
        with set_chip_context("core"):
            test_attribution()
        print("\n--- TEST COMPLETED ---")
    except Exception as e:
        print(f"\n--- TEST FAILED: {e} ---")
        import traceback
        traceback.print_exc()
