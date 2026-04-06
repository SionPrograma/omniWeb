
import sys
import os
sys.path.append(os.getcwd())

from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.ai_host.memory.persona_simulator import persona_simulator
from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.permissions import set_chip_context

def validate_persona_sim():
    print("--- VALIDATING MULTI-PERSONA SIMULATION ---")
    
    with set_chip_context("core", user_id="1"):
        # 1. Create a test branch
        branch = branch_manager.create_branch("Test Persona Sim", origin="main")
        branch_id = branch.branch_id
        print(f"Created branch: {branch_id}")
        
        # 2. Add some specific missions to trigger reactions
        # High risk core mission -> Should trigger Architect/Auditor friction
        handoff_manager.add_proposal({
            "objective": "Heavy Refactor of DB Core without tests",
            "surface_affected": ["db", "core"],
            "risk_level": "high",
            "origin_persona": "ARCHITECT"
        })
        # Update branch_id for these missions (manual override for test)
        from backend.core.database import db_manager
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE mission_handoffs SET branch_id = ? WHERE objective LIKE '%Heavy Refactor%'", (branch_id,))
            conn.commit()

        # 3. Run simulation
        report = persona_simulator.simulate_branch_reaction(branch_id)
        
        print(f"\nConsensus: {report.global_consenus}")
        print(f"Summary: {report.summary}")
        
        for r in report.responses:
            print(f"\n[{r.role}] Support: {r.support_score:.2f}, Friction: {r.friction_score:.2f}")
            print(f"Rationale: {r.rationale}")
            if r.recommendation:
                print(f"REC: {r.recommendation}")

        # 4. Clean up
        branch_manager.delete_branch(branch_id)
        print("\nCleanup complete.")

if __name__ == "__main__":
    validate_persona_sim()
