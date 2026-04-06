import asyncio
import sys
import os

# Add project root to path
sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.permissions import set_chip_context

async def test():
    with set_chip_context("core"):
        orch = CognitiveOrchestrator()
        
        # 1. Create a handoff for testing
        h = handoff_manager.add_proposal({"objective": "Test Task 1", "surface_affected": ["core"]}, source="test")
        print(f"Created Handoff: {h.handoff_id}")
        
        # 2. Simulate CREATE command
        res = await orch.orchestrate("CREATE MISSION SCHEDULE", {"intent_group": "MISSION_INTENT", "mode": "technical"})
        print(f"Create Result: {res.message}")
        
        # 3. Simulate ADD command
        res = await orch.orchestrate(f"ADD TO MISSION SCHEDULE HANDOFF {h.handoff_id}", {"intent_group": "MISSION_INTENT", "mode": "technical"})
        print(f"Add Result: {res.message}")
        
        # 4. Simulate SHOW command
        res = await orch.orchestrate("SHOW MISSION SCHEDULE", {"intent_group": "MISSION_INTENT", "mode": "technical"})
        print(f"Show Result Payload has schedules: {'schedules' in res.payload['tactical_overlay']}")
        
        if len(res.payload['tactical_overlay']['schedules']) > 0:
            sched = res.payload['tactical_overlay']['schedules'][0]
            print(f"Schedule Name: {sched['name']}")
            print(f"Missions in schedule: {len(sched['missions'])}")

if __name__ == "__main__":
    asyncio.run(test())
