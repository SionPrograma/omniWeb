import asyncio
import json
import uuid
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.cross_branch_engine import branch_synergy_engine

async def validate_consolidation():
    print("--- VALIDATING REDUNDANT BRANCH CONSOLIDATION FLOW ---")
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 1. Cleanup
            conn.execute("DELETE FROM branch_consolidations")
            conn.execute("DELETE FROM branch_synergy_relations")
            conn.execute("DELETE FROM mission_handoffs WHERE branch_id IN ('br_cons_a', 'br_cons_b')")
            conn.execute("DELETE FROM roadmap_branches WHERE branch_id IN ('br_cons_a', 'br_cons_b')")
            
            # 2. Branch A and B: Highly redundant
            # 100% surface overlap + similar objective
            conn.execute("INSERT INTO roadmap_branches (branch_id, name, branch_state) VALUES ('br_cons_a', 'Branch A', 'ACTIVE')")
            conn.execute("INSERT INTO roadmap_branches (branch_id, name, branch_state) VALUES ('br_cons_b', 'Branch B', 'ACTIVE')")
            
            obj = "Mejorar el sistema de logs para auditoría forense."
            surfaces = json.dumps(["logs", "forensics"])
            
            conn.execute("INSERT INTO mission_handoffs (handoff_id, briefing_title, objective, surface_affected, branch_id) VALUES (?, ?, ?, ?, ?)", 
                         (str(uuid.uuid4()), "Logs Alpha", obj, surfaces, "br_cons_a"))
            conn.execute("INSERT INTO mission_handoffs (handoff_id, briefing_title, objective, surface_affected, branch_id) VALUES (?, ?, ?, ?, ?)", 
                         (str(uuid.uuid4()), "Logs Beta", obj, surfaces, "br_cons_b"))
            
            conn.commit()

    print("Branches seeded. Running synergy scan (should trigger consolidation engine)...")
    branch_synergy_engine.scan_active_branches()
    
    # 3. Check for proposals
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            proposals = conn.execute("SELECT * FROM branch_consolidations").fetchall()
            
    print(f"FOUND {len(proposals)} consolidation proposals.")
    for p in proposals:
        print(f"[{p['state']}] {p['primary_branch_id']} <-> {p['secondary_branch_id']}")
        print(f"    Rationale: {p['rationale']}")
        print(f"    Gain: {p['expected_gain']}")

    if len(proposals) > 0:
        print("SUCCESS: Consolidation proposed for highly redundant branches.")
    else:
        print("FAIL: Consolidation NOT proposed.")

if __name__ == "__main__":
    asyncio.run(validate_consolidation())
