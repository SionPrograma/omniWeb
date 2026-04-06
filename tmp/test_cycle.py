import asyncio
import sys
import os

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

import backend.core.permissions
def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager

async def test_cycle():
    # A touches A, mentions B (depends on B)
    # B touches B, mentions A (depends on A)
    h_a = handoff_manager.add_proposal({"objective": "Upgrade B infra", "surface_affected": ["A"]}, source="test")
    h_b = handoff_manager.add_proposal({"objective": "Patch A system", "surface_affected": ["B"]}, source="test")
    
    sched = scheduler_manager.create_schedule("Cycle Test v2", [h_a.handoff_id, h_b.handoff_id])
    analyzed = scheduler_manager.analyze_sequence(sched.schedule_id)
    
    print("\n--- CYCLE ANALYSIS ---")
    print(f"Confidence: {analyzed.sequence_proposal.confidence}")
    print(f"Rationale: {analyzed.sequence_proposal.rationale}")
    print(f"Confidence is Low (Cycle): {analyzed.sequence_proposal.confidence < 0.5}")

if __name__ == "__main__":
    asyncio.run(test_cycle())
