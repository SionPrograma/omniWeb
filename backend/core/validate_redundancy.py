import asyncio
import json
import uuid
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.observability.cross_branch_engine import branch_synergy_engine

async def validate_redundancy():
    print("--- VALIDATING CROSS-BRANCH REDUNDANCY ---")
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # 1. Cleanup
            conn.execute("DELETE FROM branch_synergy_relations")
            conn.execute("DELETE FROM mission_handoffs WHERE branch_id IN ('br_r_a', 'br_r_b')")
            conn.execute("DELETE FROM roadmap_branches WHERE branch_id IN ('br_r_a', 'br_r_b')")
            
            # 2. Branch A: Optimización de Base de Datos
            conn.execute("""
                INSERT INTO roadmap_branches (branch_id, name, branch_state) 
                VALUES ('br_r_a', 'Optimización DB', 'ACTIVE')
            """)
            conn.execute("""
                INSERT INTO mission_handoffs (handoff_id, briefing_title, objective, surface_affected, branch_id)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), "Index optimization", "Optimizar los índices de la base de datos para mejorar el rendimiento de las consultas pesadas.", json.dumps(["database", "performance"]), "br_r_a"))

            # 3. Branch B: DB Performance Boost (REDUNDANT)
            conn.execute("""
                INSERT INTO roadmap_branches (branch_id, name, branch_state) 
                VALUES ('br_r_b', 'DB Boost', 'ACTIVE')
            """)
            conn.execute("""
                INSERT INTO mission_handoffs (handoff_id, briefing_title, objective, surface_affected, branch_id)
                VALUES (?, ?, ?, ?, ?)
            """, (str(uuid.uuid4()), "DB Tuning", "Mejorar el rendimiento de las consultas pesadas optimizando los índices y el esquema de la base de datos.", json.dumps(["database"]), "br_r_b"))
            
            conn.commit()

    print("Branches seeded. Running scan...")
    relations = branch_synergy_engine.scan_active_branches()
    
    for r in relations:
        print(f"[{r.relation_type}] {r.branch_a_id} vs {r.branch_b_id}")
        print(f"    Rationale: {r.rationale}")

    if any(r.relation_type == "REDUNDANCY" for r in relations):
        print("SUCCESS: Redundancy detected.")
    else:
        print("FAIL: Redundancy NOT detected.")

if __name__ == "__main__":
    asyncio.run(validate_redundancy())
