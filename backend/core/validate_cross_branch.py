import asyncio
import json
import uuid
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.cross_branch_engine import branch_synergy_engine

async def validate_cross_branch():
    print("--- VALIDATING CROSS-BRANCH SYNERGY ANALYSIS ---")
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 1. Cleanup existing branches for clean test
            conn.execute("DELETE FROM branch_synergy_relations")
            conn.execute("DELETE FROM mission_handoffs WHERE branch_id IN ('br_test_a', 'br_test_b')")
            conn.execute("DELETE FROM roadmap_branches WHERE branch_id IN ('br_test_a', 'br_test_b')")
            
            # 2. Create Branch A: Refactor Auth
            conn.execute("""
                INSERT INTO roadmap_branches (branch_id, name, branch_state) 
                VALUES ('br_test_a', 'Branch Refactor Auth', 'ACTIVE')
            """)
            conn.execute("""
                INSERT INTO mission_handoffs (handoff_id, briefing_title, objective, surface_affected, branch_id)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), "Refactor Core Auth", "Refactorizar el sistema de login y JWT.", json.dumps(["auth", "router"]), "br_test_a"))

            # 3. Create Branch B: Delete Auth (COLLISION)
            conn.execute("""
                INSERT INTO roadmap_branches (branch_id, name, branch_state) 
                VALUES ('br_test_b', 'Branch Purge Auth', 'ACTIVE')
            """)
            conn.execute("""
                INSERT INTO mission_handoffs (handoff_id, briefing_title, objective, surface_affected, branch_id)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), "Purge Legacy Auth", "Borrar el viejo sistema de auth por obsolescencia.", json.dumps(["auth"]), "br_test_b"))
            
            conn.commit()

    print("Branches seeded. Running cross-branch scan...")
    
    # 4. Run Scan
    relations = branch_synergy_engine.scan_active_branches()
    
    print(f"SCAN COMPLETED: Found {len(relations)} relations.")
    for r in relations:
        print(f"[{r.relation_type}] Branch A: {r.branch_a_id} vs Branch B: {r.branch_b_id}")
        print(f"    Rationale: {r.rationale}")
        print(f"    Action: {r.recommended_action}")

    if any(r.relation_type == "COLLISION" for r in relations):
        print("SUCCESS: Collision detected between Refactor and Purge.")
    else:
        print("FAIL: Collision NOT detected.")

if __name__ == "__main__":
    asyncio.run(validate_cross_branch())
