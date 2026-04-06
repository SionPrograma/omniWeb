import asyncio
import sys

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
import backend.core.permissions

def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

async def test_atomic_push():
    print("\n--- ATOMIC PUSH EXECUTION STRESS TEST ---")
    
    # 1. Fetch group
    macro = roadmap_aggregator.get_macro_roadmap()
    ui_group = next((g for g in macro.groups if g.group_id == 'surface_ui'), None)
    if not ui_group:
        print("No UI surface found. Run test_readiness.py first.")
        return

    # 2. Start Session
    print(f"Starting Atomic Push for {ui_group.group_id}...")
    session = roadmap_aggregator.start_push_session(ui_group.group_id)
    print(f"Session ID: {session.push_id} | State: {session.state} | Steps: {len(session.steps)}")

    # 3. Step Through
    for _ in range(len(session.steps) + 1):
        print(f"\nExecuting Step {session.current_step_index + 1}...")
        session = roadmap_aggregator.execute_next_step(session.push_id)
        
        step_statuses = [s.status for s in session.steps]
        print(f" - Status: {session.state}")
        print(f" - Steps progress: {step_statuses}")
        
        if session.state in ["COMPLETED", "BLOCKED", "FAILED_SAFELY"]:
            break

    # 4. TRACEABILITY CHECK
    print("\n--- TRACEABILITY REPORT ---")
    final_session = roadmap_aggregator.get_session(session.push_id)
    print(f"Session State: {final_session.state}")
    print(f"Blocking Reason: {final_session.blocking_reason}")
    print(f"Authority Req: {final_session.authority_required}")
    for s in final_session.steps:
        print(f" [{s.type}] {s.handoff_id[:6]} -> {s.status} (Error: {s.error})")

if __name__ == "__main__":
    asyncio.run(test_atomic_push())
