import asyncio
import sys
import os

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

import backend.core.permissions
def mock_enforce(perm): return True
backend.core.permissions.enforce_permission = mock_enforce

from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.database import db_manager
from datetime import datetime

async def test_strategic_foreclosure():
    print("\n--- STRATEGIC FORECLOSURE STRESS TEST ---")
    
    # 1. Setup Dummy Mission for foreign keys
    with db_manager.get_connection() as conn:
        try:
            conn.execute("INSERT INTO system_missions (mission_id, active_goal, status) VALUES (?, ?, ?)", 
                        ("test-dummy", "Dummy Goal", "COMPLETED"))
            conn.commit()
        except: pass # already exists
        
        # Insert telemetry for h3 to be obsolete
        conn.execute("INSERT INTO system_mission_telemetry (mission_id, event_type, message, timestamp) VALUES (?, ?, ?, ?)", 
                    ("test-dummy", "MISSION_COMPLETED", "Fix sidebar bug", datetime.now().isoformat()))
        conn.commit()

    # 2. Setup Scenario:
    h1 = handoff_manager.add_proposal(
        {"objective": "Update auth schema legacy", "surface_affected": ["auth"], "risk_level": "low"},
        source="test_legacy"
    )
    
    h2 = handoff_manager.add_proposal(
        {"objective": "Update auth schema v2 critical", "surface_affected": ["auth"], "risk_level": "medium"},
        source="test_new"
    )
    
    h3 = handoff_manager.add_proposal(
        {"objective": "Fix sidebar bug", "surface_affected": ["frontend"]},
        source="test_obsolete"
    )

    # 3. RUN AUDIT
    print("Running Foreclosure Audit...")
    audited = handoff_manager.audit_foreclosure()
    
    h1_after = next(m for m in audited if m.handoff_id == h1.handoff_id)
    h3_after = next(m for m in audited if m.handoff_id == h3.handoff_id)
    
    print(f"Mission 1 (Legacy): Status={h1_after.foreclosure.status}, Reason={h1_after.foreclosure.reason}")
    print(f"Mission 3 (Obsolete): Status={h3_after.foreclosure.status}, Reason={h3_after.foreclosure.reason}")
    
    # 4. APPLY FORECLOSURE
    print("\nApplying Foreclosure to Mission 3...")
    handoff_manager.foreclose_proposal(h3.handoff_id, "Confirmado por el Creador", "FORECLOSE")
    
    # 5. VERIFY BACKLOG & HISTORY
    active = handoff_manager.get_all(include_archived=False)
    archived = handoff_manager.get_all(include_archived=True)
    
    h3_final = next(m for m in archived if m.handoff_id == h3.handoff_id)
    
    print(f"Active Queue Size: {len(active)}")
    print(f"Mission 3 in Final History: State={h3_final.readiness_state}, Foreclosure={h3_final.foreclosure.status}")
    
    # 6. REACTIVATION
    print("\nReactivating Mission 3...")
    handoff_manager.reactivate_handoff(h3.handoff_id)
    active_now = handoff_manager.get_all(include_archived=False)
    h3_reactivated = next(m for m in active_now if m.handoff_id == h3.handoff_id)
    print(f"Mission 3 Reactivated State: {h3_reactivated.reactivation_state if hasattr(h3_reactivated, 'reactivation_state') else h3_reactivated.readiness_state}, Foreclosure={h3_reactivated.foreclosure.status}")

if __name__ == "__main__":
    asyncio.run(test_strategic_foreclosure())
