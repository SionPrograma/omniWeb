import sys
import os
import json
from datetime import datetime

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus
from backend.core.ai_host.memory.resource_lock_manager import resource_lock_manager

def validate_priority_engine():
    print("--- VALIDATING MISSION SCHEDULING & PRIORITY ENGINE ---")
    
    with set_chip_context("core"):
        # 1. Apply Migrations
        print("Applying migrations...")
        db_manager.run_migrations()
        
        # 2. Cleanup previous test missions if any
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM system_missions WHERE active_goal LIKE 'TEST_PRIORITY_%'")
            conn.execute("DELETE FROM system_locks WHERE mission_id LIKE 'test_m_%'")
            conn.commit()

        # 3. Create Scenarios
        print("\nCreating operational scenarios...")
        
        # M1: Normal Mission (OPEN)
        m1 = mission_manager.create_mission("TEST_PRIORITY_NORMAL: Refactor CSS")
        
        # M2: Critical Mission (Risk Limit Reached) -> Should be URGENT
        m2 = mission_manager.create_mission("TEST_PRIORITY_CRITICAL: Core Kernel Patch")
        m2.parameters["risk_budget"] = 10.0
        m2.parameters["risk_consumed"] = 10.5 # Exceeded
        m2.status = MissionStatus.PAUSED
        m2.blocked_reasons.append("AUTONOMÍA EXCEDIDA: Requiere PIN.")
        mission_manager.save_mission(m2)
        
        # M3: Blocked Mission (Resource Conflict) -> Should be DEFERRED/WAITING
        m3 = mission_manager.create_mission("TEST_PRIORITY_BLOCKED: Database Tuning")
        resource_lock_manager.acquire_lock("system_db", "other_mission_id", reason="En mantenimiento")
        m3.status = MissionStatus.BLOCKED
        m3.blocked_reasons.append("CONFLICT: Module 'system_db' locked by other_mission_id")
        mission_manager.save_mission(m3)
        
        # M4: Focused Mission (Creator Focus) -> Should be HIGH
        m4 = mission_manager.create_mission("TEST_PRIORITY_FOCUS: UI Polish")
        mission_manager.active_mission = m4 # Set focus
        
        # 4. Run Ranking
        print("\nRanking portfolio...")
        ranking = mission_manager.get_parallel_running_missions()
        
        print("\nRANKING RESULTS:")
        for i, m in enumerate(ranking):
            print(f"{i+1}. [{m.priority_class}] (Score: {m.priority_score}) {m.active_goal}")
            print(f"   Status: {m.status.value} | Readiness: {m.readiness_state}")
        
        # 5. Verify expectations
        top_mission = ranking[0]
        assert top_mission.priority_class == "URGENT", "Top mission should be URGENT due to risk limit"
        
        deferred = [m for m in ranking if m.readiness_state == "WAITING_RESOURCE"]
        assert len(deferred) > 0, "Mission M3 should be tagged as WAITING_RESOURCE"
        
        print("\n--- VALIDATION SUCCESSFUL ---")
        print(f"Top Recommendation: {top_mission.active_goal} ({top_mission.priority_class})")

if __name__ == "__main__":
    try:
        validate_priority_engine()
    except Exception as e:
        print(f"\n--- VALIDATION FAILED: {e} ---")
        import traceback
        traceback.print_exc()
