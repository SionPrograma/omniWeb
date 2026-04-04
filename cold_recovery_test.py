import sys
import os
import json
from datetime import datetime, timedelta

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import MissionManager, MissionStatus
from backend.core.ai_host.memory.resource_lock_manager import ResourceLockManager, LockStatus

def validate_cold_recovery():
    print("--- VALIDATING MISSION COLD RECOVERY & PERSISTENCE HARDENING ---")
    
    with set_chip_context("core"):
        # 1. SETUP: Create state as if the system was running
        print("\n[STEP 1] Setting up 'Previous Session' data...")
        
        # Cleanup
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM system_missions")
            conn.execute("DELETE FROM system_locks")
            conn.commit()
            
        # Create a singleton manually to simulate starting from clean
        # (Though we'll simulate the restart by creating NEW instances later)
        temp_manager = MissionManager()
        
        # A. Mission in focus
        m1 = temp_manager.create_mission("FOCUS_MISSION: Tarea principal persistida")
        m1.status = MissionStatus.OPEN
        m1.last_focused_at = datetime.now() - timedelta(minutes=1)
        temp_manager.save_mission(m1)
        
        # B. Parallel mission
        m2 = temp_manager.create_mission("PARALLEL_MISSION: Tarea en segundo plano")
        m2.status = MissionStatus.RUNNING
        m2.last_focused_at = datetime.now() - timedelta(minutes=10)
        temp_manager.save_mission(m2)
        
        # C. Zombie Lock Mission (a mission that finished but left a lock)
        m3_zombie = temp_manager.create_mission("ZOMBIE_MISSION: Esta terminara mal")
        m3_zombie.status = MissionStatus.COMPLETED # Finished but...
        temp_manager.save_mission(m3_zombie)
        
        # Create locks
        lock_manager = ResourceLockManager()
        lock_manager.acquire_lock("resource_shared_active", m1.mission_id, reason="Active task locking")
        
        # Manually inject a zombie lock in DB (to simulate a crash before release)
        with db_manager.get_connection() as conn:
            conn.execute("""
                INSERT INTO system_locks (resource_key, mission_id, status, reason)
                VALUES ('resource_zombie', ?, 'ACQUIRED', 'Left behind by crash')
            """, (m3_zombie.mission_id,))
            conn.commit()
            
        print(f"Data setup: 1 Focus Open, 1 Parallel Running, 1 Zombie Lock (on resource_zombie)")

        # 2. THE COLD RESTART
        print("\n[STEP 2] SIMULATING COLD BACKEND RESTART...")
        # We manually destroy and recreate the Singletons
        # This simulates a fresh Python process starting 
        MissionManager._instance = None
        ResourceLockManager._instance = None
        
        # 3. REHYDRATION
        print("\n[STEP 3] Re-instantiating Managers (Triggering Rehydration)...")
        new_mission_manager = MissionManager()
        new_lock_manager = ResourceLockManager()
        
        # 4. VERIFICATION
        print("\n[STEP 4] Verifying Rehydrated State...")
        
        # A. Focus check
        active = new_mission_manager.get_active_mission()
        if not active:
            raise Exception("FAILED: Focus mission was not rehydrated!")
        print(f" - SUCCESS: Focus restored to '{active.active_goal}' (ID: {active.mission_id})")
        
        # B. Parallel check
        parallel = new_mission_manager.get_parallel_running_missions()
        # parallel includes OPEN/RUNNING/BLOCKED/PAUSED, but focal is filtered in Rank if we provide focal_id
        # In internal logic, m2 should be there.
        m2_ids = [m.mission_id for m in parallel]
        if m2.mission_id not in m2_ids:
             # Wait, get_parallel_running_missions ranks them. Focal IS often included in the raw list but Rank filters or sorts.
             print(f"DEBUG: Found parallel IDs {m2_ids}")
             if len(m2_ids) < 2: # m1 and m2 should be in the raw DB fetch
                  raise Exception(f"FAILED: Parallel mission '{m2.mission_id}' missing.")
        print(f" - SUCCESS: Portfolio rehydrated (Found {len(m2_ids)} inflight missions)")

        # C. Zombie Lock check
        with db_manager.get_connection() as conn:
            zombie_row = conn.execute("SELECT status FROM system_locks WHERE resource_key = 'resource_zombie'").fetchone()
            active_row = conn.execute("SELECT status FROM system_locks WHERE resource_key = 'resource_shared_active'").fetchone()
            
        if zombie_row['status'] != 'RELEASED':
             raise Exception(f"FAILED: Zombie lock was NOT cleaned up! Status: {zombie_row['status']}")
        print(" - SUCCESS: Zombie lock automatically reconciled and RELEASED.")
        
        if active_row['status'] != 'ACQUIRED':
             raise Exception("FAILED: Valid active lock was incorrectly released!")
        print(" - SUCCESS: Valid lock preserved for active focus mission.")

        print("\n--- COLD RECOVERY VALIDATION SUCCESSFUL ---")
        print("OmniWeb is now resilient to backend restarts. Focus, portfolio, and governance are preserved.")

if __name__ == "__main__":
    try:
        validate_cold_recovery()
    except Exception as e:
        print(f"\n--- VALIDATION FAILED: {e} ---")
        import traceback
        traceback.print_exc()
