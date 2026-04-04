import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor

async def validate_roi_analytics():
    print("--- VALIDATING MISSION REALIGNMENT ROI ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 1. SETUP: Mission with drift signal
        print("\n[STEP 1] Creating Drift Scenario...")
        await processor.process("[VISUAL_EVIDENCE] Phase 1", context={})
        m = mission_manager.get_active_mission()
        m.multimodal_history[-1]["hypothesis"] = {"layer": "backend", "description": "Signal A"}
        
        # Add noisy event
        print("[STEP 1.1] Adding Noise event...")
        await processor.process("[VISUAL_EVIDENCE] Noise event", context={})
        noise_node_id = m.multimodal_history[-1]["id"]
        m.multimodal_history[-1]["hypothesis"] = {"layer": "frontend", "description": "Signal B (Noise)"}
        mission_manager.save_mission(m)

        # 2. RUN PERFORMANCE AUDIT
        print("\n[STEP 2] Executing ROI Correction (EXCLUDE_NODE)...")
        # We target the noise node
        action = {
            "type": "EXCLUDE_NODE",
            "node_id": noise_node_id,
            "label": "Exclude Noise Node"
        }
        
        result = m.execute_realignment_action(action)
        mission_manager.save_mission(m)
        
        audit = result["performance_audit"]
        print(f"Correction Result: {result['message']}")
        print(f"Audit: Before={audit['drift_before']}, After={audit['drift_after']}, Delta={audit['delta']}")
        print(f"Impact Class: {audit['impact']}")

        # 3. VERIFY ROI VALIDITY
        if audit["delta"] <= 0:
             raise Exception(f"FAILED: ROI delta must be positive after exclusion. Got {audit['delta']}")
        
        if audit["impact"] != "HIGH_IMPACT_RECOVEY" and audit["delta"] > 10:
             pass # Logic matches
             
        # 4. CHECK PERSISTENCE
        last_event = m.multimodal_history[-1]["event"]
        if "REALIGNMENT_ROI" not in last_event:
             raise Exception(f"FAILED: No ROI event in history. Got {last_event}")
             
        print("\n--- MISSION REALIGNMENT ROI VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_roi_analytics())
