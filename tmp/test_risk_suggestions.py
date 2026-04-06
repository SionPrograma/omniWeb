import asyncio
import sys
import os

# Add project root to path
sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

import backend.core.permissions
def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager

async def test_risk():
    # 1. Create two high risk handoffs
    h1 = handoff_manager.add_proposal({"objective": "Delete DB", "risk_level": "high", "surface_affected": ["db"]}, source="test")
    h2 = handoff_manager.add_proposal({"objective": "Wipe Cache", "risk_level": "high", "surface_affected": ["cache"]}, source="test")
    
    # 2. Create schedule
    sched = scheduler_manager.create_schedule("Risk Chain Test", [h1.handoff_id, h2.handoff_id])
    
    # 3. Analyze
    analyzed = scheduler_manager.analyze_sequence(sched.schedule_id)
    
    print("\n--- RISK ANALYSIS ---")
    print(f"Risk Chain: {analyzed.risk_chain}")
    print(f"Suggestions: {[s.label for s in analyzed.suggestions]}")
    
    found_split = any(s.type == "RISK_SPLIT" for s in analyzed.suggestions)
    print(f"Risk Split suggestion found: {found_split}")

if __name__ == "__main__":
    asyncio.run(test_risk())
