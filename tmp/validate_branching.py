import asyncio
import sys
import json
from datetime import datetime

sys.path.append(r'c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb')

from backend.core.ai_host.memory.branch_manager import branch_manager
from backend.core.ai_host.memory.handoff_manager import handoff_manager
from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
from backend.core.permissions import set_chip_context

async def validate_mission_branching():
    print("\n--- OMNIWEB: MISSION EVOLUTION & BRANCHING VALIDATION ---")
    
    with set_chip_context("core"):
        # 1. Baseline: Ensure main has at least one mission
        main_missions = handoff_manager.get_all(branch_id="main")
        if not main_missions:
            print("Seeding main mission for test...")
            handoff_manager.add_proposal({"objective": "Main Baseline Mission"})
            main_missions = handoff_manager.get_all(branch_id="main")
        
        print(f"Main missions: {len(main_missions)}")
        
        # 2. Create branch
        print("Creating experimental branch 'Experiment A'...")
        branch = branch_manager.create_branch("Experiment A", origin="main")
        print(f"Branch created: {branch.branch_id}")
        
        # 3. Modify branch
        print("Adding mission to branch 'Experiment A'...")
        # We need a way to add a mission to a specific branch. 
        # I'll manually call add_proposal and then update its branch_id since add_proposal defaults to main.
        # Actually, let's update add_proposal to support branch_id too.
        prop = handoff_manager.add_proposal({"objective": "Experimental Mission Only for Branch"})
        handoff_manager.update_proposal(prop.handoff_id, {"branch_id": branch.branch_id})
        
        # 4. Verify Independence
        branch_missions = handoff_manager.get_all(branch_id=branch.branch_id)
        current_main_missions = handoff_manager.get_all(branch_id="main")
        
        print(f"Branch missions: {len(branch_missions)}")
        print(f"Main missions after branch mod: {len(current_main_missions)}")
        
        assert len(branch_missions) == len(main_missions) + 1
        assert len(current_main_missions) == len(main_missions)
        print("PASS: Branch isolation confirmed.")
        
        # 5. Merge Governance
        print("Merging 'Experiment A' into main...")
        merge_result = branch_manager.merge_branch(branch.branch_id, target="main")
        print(f"Merge outcome: {merge_result['status']}")
        
        final_main = handoff_manager.get_all(branch_id="main")
        print(f"Final Main missions: {len(final_main)}")
        assert len(final_main) == len(branch_missions)
        print("PASS: Governed merge successful.")
        
        # 6. Discarding
        print("Creating 'Experiment B' to discard...")
        branch_b = branch_manager.create_branch("Experiment B", origin="main")
        branch_manager.delete_branch(branch_b.branch_id)
        
        branches = branch_manager.get_branches()
        branch_ids = [b.branch_id for b in branches]
        assert branch_b.branch_id not in branch_ids
        print("PASS: Branch discarding works.")

    print("\nMission Evolution & Branching validation SUCCESSFUL.")

if __name__ == "__main__":
    asyncio.run(validate_mission_branching())
