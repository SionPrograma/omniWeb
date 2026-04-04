import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor

async def validate_realignment_execution():
    print("--- VALIDATING TACTICAL REALIGNMENT EXECUTION ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 1. SETUP: Create mission with drift
        print("\n[STEP 1] Creating Mission with Drift...")
        await processor.process("[VISUAL_EVIDENCE] Initial", context={})
        m = mission_manager.get_active_mission()
        m.active_goal = "Core Backend Implementation"
        m.multimodal_history[-1]["hypothesis"] = {"layer": "backend/core", "description": "Backend focus"}
        
        # Add drift
        print("[STEP 1.1] Adding Drift signal...")
        await processor.process("[VISUAL_EVIDENCE] UI shift", context={})
        m.multimodal_history[-1]["hypothesis"] = {"layer": "frontend/css", "description": "CSS focus"}
        mission_manager.save_mission(m)

        # 2. ANALYZE AND GET SUGGESTION
        print("\n[STEP 2] Analyzing Drift and fetching suggested actions...")
        report = m.analyze_cognitive_drift()
        actions = report["suggested_actions"]
        
        restore_action = next((a for a in actions if a["type"] == "RESTORE_FOCUS"), None)
        if not restore_action:
             raise Exception("FAILED: RESTORE_FOCUS action not suggested for critical drift.")
        
        print(f"Found executable action: {restore_action['label']}")

        # 3. EXECUTE ACTION
        print("\n[STEP 3] Executing Realignment Action...")
        result = m.execute_realignment_action(restore_action)
        mission_manager.save_mission(m)
        
        if not result["success"]:
             raise Exception(f"FAILED: Action execution failed: {result['message']}")
        
        print(f"Correction Result: {result['message']}")

        # 4. VERIFY STATE
        print("\n[STEP 4] Verifying mission state after correction...")
        m_after = mission_manager.get_mission(m.mission_id)
        
        # Check active_goal marker
        if "[RESTORED]" not in m_after.active_goal:
             raise Exception("FAILED: active_goal does not contain [RESTORED] marker.")
             
        # Check history event
        last_event = m_after.multimodal_history[-1]
        if "FOCUS_RESTORED" not in last_event["event"]:
             raise Exception("FAILED: Correction event not found in multimodal history.")
             
        # Check drift reset latch
        if m_after.parameters.get("last_alerted_drift") != "ALIGNED":
             raise Exception("FAILED: last_alerted_drift latch not reset.")

        print("\n--- TACTICAL REALIGNMENT VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_realignment_execution())
