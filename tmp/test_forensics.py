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

async def test_forensics():
    print("\n--- TACTICAL TELEMETRY & FORENSICS TEST ---")
    
    with set_chip_context("core"):
        # 1. Create a blocked handoff
        print("Creating mission with PIN block...")
        h = handoff_manager.add_proposal({
            "objective": "Forensics Test Mission",
            "surface_affected": ["core"],
            "risk_level": "critical"
        }, gate={"type": "PIN", "required": True})
        
        # 2. Start Push
        session = roadmap_aggregator.start_push_session("surface_core")
        push_id = session.push_id
        
        # 3. Step until blocked
        while session.state in ["RUNNING", "READY"] and session.current_step_index < len(session.steps):
            session = roadmap_aggregator.execute_next_step(push_id)
            if session.state == "BLOCKED": break

        # 4. Inject Authority
        print("Injecting Authority (Correct PIN)...")
        session = roadmap_aggregator.inject_authority(push_id, "1234")
        
        # 5. Complete
        while session.state == "RUNNING":
            session = roadmap_aggregator.execute_next_step(push_id)
            
        print(f"Final session state: {session.state}")

        # 6. RETRIEVE FORENSICS
        print("\n--- RETRIEVING FORENSICS ---")
        history = roadmap_aggregator.get_forensics(push_id)
        
        event_types = [e["event_type"] for e in history]
        print(f"Events captured: {event_types}")
        
        # ASSERTS
        assert "PUSH_STARTED" in event_types
        assert "STEP_BLOCKED" in event_types
        assert "AUTHORITY_INJECTED" in event_types
        assert "PUSH_COMPLETED" in event_types
        
        for e in history:
            print(f" [{e['timestamp']}] {e['event_type']} (Hash: {e['integrity_hash'][:8]}...)")
            # Verify payload is JSON
            json.loads(e["payload"])

        print("\nForensics validation SUCCESSFUL.")
        
        # CLEANUP
        handoff_manager.delete_proposal(h.handoff_id)

if __name__ == "__main__":
    asyncio.run(test_forensics())
