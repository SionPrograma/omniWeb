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

async def test_authority_hud():
    print("\n--- AUTHORITY HUD INTEGRATION TEST ---")
    
    with set_chip_context("core"):
        # 1. Create a blocked handoff
        print("Creating mission with PIN block...")
        h = handoff_manager.add_proposal({
            "objective": "Critical Core Update (Requires PIN)",
            "surface_affected": ["core"],
            "risk_level": "critical"
        }, gate={"type": "PIN", "required": True})
        
        # 2. Start Push session for core
        print(f"Starting Atomic Push for surface_core...")
        session = roadmap_aggregator.start_push_session("surface_core")
        
        # 3. Step until blocked
        print("Executing steps...")
        for _ in range(len(session.steps)):
            session = roadmap_aggregator.execute_next_step(session.push_id)
            if session.state == "BLOCKED":
                break
        
        print(f"Session State: {session.state}")
        print(f"Is Resolvable: {session.is_resolvable}")
        print(f"Blocking Reason: {session.blocking_reason}")
        
        if not session.is_resolvable:
            print("ERROR: Session should be resolvable.")
            return

        # 4. Inject WRONG PIN
        print("\nInjecting WRONG PIN (0000)...")
        try:
            roadmap_aggregator.inject_authority(session.push_id, "0000")
        except ValueError as e:
            print(f" Expected Error: {e}")

        # 5. Inject CORRECT PIN (1234)
        print("Injecting CORRECT PIN (1234)...")
        session = roadmap_aggregator.inject_authority(session.push_id, "1234")
        print(f"Session State after injection: {session.state}")
        
        # 6. Step until complete
        while session.state == "RUNNING":
            session = roadmap_aggregator.execute_next_step(session.push_id)
            
        print(f"Final State: {session.state}")
        
        # CLEANUP
        handoff_manager.delete_proposal(h.handoff_id)

if __name__ == "__main__":
    asyncio.run(test_authority_hud())
