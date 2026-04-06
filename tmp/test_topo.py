import asyncio
import sys
import os

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

import backend.core.permissions
def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager

async def test_topo():
    h_a = handoff_manager.add_proposal({"objective": "Base Infrastructure Setup", "surface_affected": ["infra"]}, source="test")
    h_b = handoff_manager.add_proposal({"objective": "Refactor based on infra changes", "surface_affected": ["core"]}, source="test")
    
    sched = scheduler_manager.create_schedule("Topo Logic Test", [h_b.handoff_id, h_a.handoff_id])
    analyzed = scheduler_manager.analyze_sequence(sched.schedule_id)
    
    print("\n--- TOPO ANALYSIS ---")
    print(f"Current Order: {[h[:6] for h in analyzed.ordered_handoff_ids]}")
    print(f"Suggested Order: {[h[:6] for h in analyzed.recommended_sequence]}")
    
    is_corrected = analyzed.recommended_sequence[0] == h_a.handoff_id
    print(f"Correction successful (A before B): {is_corrected}")
    print(f"Rationale: {analyzed.sequence_proposal.rationale}")

if __name__ == "__main__":
    asyncio.run(test_topo())
