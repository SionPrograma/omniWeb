import asyncio
import sys
import json

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.permissions import set_chip_context
import backend.core.permissions

def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

async def test_rollback():
    print("\n--- GOVERNED ROLLBACK LOGIC TEST ---")
    
    with set_chip_context("core"):
        # 1. Setup a mission and a successful push
        print("Setup: Creating mission and push...")
        h = handoff_manager.add_proposal({
            "objective": "Rollback Test",
            "surface_affected": ["core"],
            "risk_level": "low"
        })
        
        session = roadmap_aggregator.start_push_session("surface_core")
        push_id = session.push_id
        
        while session.state in ["RUNNING", "READY"]:
            session = roadmap_aggregator.execute_next_step(push_id)
            if session.state == "COMPLETED": break
            
        print(f"Push {push_id} completed. Mission state: {h.readiness_state}")
        # Refresh handoff state
        h = handoff_manager.get_proposal(h.handoff_id)
        print(f"Post-Push state: {h.readiness_state}")
        assert h.readiness_state == "PENDING"

        # 2. GENERATE ROLLBACK PREVIEW
        print("\nGenerating Rollback Preview...")
        rollback = roadmap_aggregator.preview_rollback(push_id)
        print(f"Rollback ID: {rollback.rollback_id}")
        print(f"Steps to revert: {len(rollback.steps)}")
        for i, s in enumerate(rollback.steps):
            print(f"  Step {i}: {s.original_step_type} on {s.handoff_id} (Revertible: {s.revertible})")

        # 3. EXECUTE ROLLBACK
        print("\nStarting Rollback...")
        rollback = roadmap_aggregator.start_rollback(rollback.rollback_id)
        
        while rollback.state == "RUNNING":
            rollback = roadmap_aggregator.execute_next_rollback_step(rollback.rollback_id)
            
        print(f"Rollback {rollback.rollback_id} final state: {rollback.state}")
        assert rollback.state == "COMPLETED"

        # 4. VALIDATE FINAL STATE
        h_final = handoff_manager.get_proposal(h.handoff_id)
        print(f"Final mission state: {h_final.readiness_state}")
        # Original state was READY
        assert h_final.readiness_state == "READY"
        print("Rollback validation SUCCESSFUL.")

        # CLEANUP
        handoff_manager.delete_proposal(h.handoff_id)

if __name__ == "__main__":
    asyncio.run(test_rollback())
