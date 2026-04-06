import asyncio
import sys
import os

# Add project root to path
sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

import backend.core.permissions

# Mock enforce_permission to always allow in test
def mock_enforce(perm):
    return True
backend.core.permissions.enforce_permission = mock_enforce

from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager

async def test():
    orch = CognitiveOrchestrator()
    
    # 1. Create two handoffs that touch the same surface
    h1 = handoff_manager.add_proposal({"objective": "Update UI", "surface_affected": ["core_ui"]}, source="test")
    h2 = handoff_manager.add_proposal({"objective": "Refactor UI Buttons", "surface_affected": ["core_ui"]}, source="test")
    print(f"Created Handoffs: {h1.handoff_id}, {h2.handoff_id}")
    
    # 2. Create a schedule
    sched = scheduler_manager.create_schedule("Tactical Stress Test", [h1.handoff_id, h2.handoff_id])
    print(f"Created Schedule: {sched.schedule_id}")
    
    # 3. Analyze sequence
    analyzed = scheduler_manager.analyze_sequence(sched.schedule_id)
    
    print("\n--- ANALYSIS RESULTS ---")
    print(f"Conflicts detected: {len(analyzed.conflict_chain)}")
    print(f"Suggestions count: {len(analyzed.suggestions)}")
    
    for s in analyzed.suggestions:
        print(f"Suggestion: [{s.type}] {s.label}")
        print(f"  Rationale: {s.rationale}")
        print(f"  Command: {s.action_cmd}")

    # 4. Integrate check via orchestrator (SHOW MISSION SCHEDULE)
    # Note: Orchestrate will use the real context, but we mocked enforce_permission at the module level
    res = await orch.orchestrate("SHOW MISSION SCHEDULE", {"intent_group": "MISSION_INTENT", "mode": "technical"})
    overlay = res.payload['tactical_overlay']
    sched_from_payload = overlay['schedules'][0]
    print(f"\nOrchestrator Payload has suggestions: {len(sched_from_payload['suggestions']) > 0}")
    print(f"First suggestion action: {sched_from_payload['suggestions'][0]['action_cmd']}")

if __name__ == "__main__":
    asyncio.run(test())
