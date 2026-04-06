import asyncio
import sys
import os

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

import backend.core.permissions
def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager

async def test_governance_audit():
    # 1. Create missions with diverse gating requirements
    # Mission A: touches 'auth'
    h_a = handoff_manager.add_proposal(
        {"objective": "Critical Auth Update", "surface_affected": ["auth"]},
        gate={"type": "PIN", "verified": False}, 
        source="test"
    )
    
    # Mission B: touches 'auth' too (will trigger sequential collision -> rebase required for B)
    h_b = handoff_manager.add_proposal(
        {"objective": "Second Auth Update", "surface_affected": ["auth"]},
        gate={"type": "CONFIRMATION", "required_authority": "root", "authority_session_active": False},
        source="test"
    )
    
    # 2. Create schedule
    sched = scheduler_manager.create_schedule("Governance Stress Test v2", [h_a.handoff_id, h_b.handoff_id])
    
    # 3. Analyze (Triggers Audit)
    # This should detect that h_b needs rebase because it follows h_a on the same surface
    analyzed = scheduler_manager.analyze_sequence(sched.schedule_id)
    
    print("\n--- GOVERNANCE AUDIT RESULTS ---")
    print(f"Global Readiness State: {analyzed.readiness_state}")
    
    for h_id, audit in analyzed.launch_audit.items():
        print(f"Mission {h_id[:6]}:")
        print(f"  Ready: {audit.is_ready}")
        print(f"  Blocks: {audit.blocks}")
        print(f"  Rationale: {audit.rationale}")

    is_gated = analyzed.readiness_state == "DRAFT"
    has_pin_block = "NEEDS_PIN" in analyzed.launch_audit[h_a.handoff_id].blocks
    has_rebase_block = "NEEDS_REBASE" in analyzed.launch_audit[h_b.handoff_id].blocks
    
    print(f"\nFinal Validation:")
    print(f"  System is gated: {is_gated}")
    print(f"  PIN block detected: {has_pin_block}")
    print(f"  Rebase block detected for B: {has_rebase_block}")

if __name__ == "__main__":
    asyncio.run(test_governance_audit())
