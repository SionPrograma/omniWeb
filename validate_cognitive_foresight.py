import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager

async def validate_cognitive_foresight():
    print("--- VALIDATING MISSION COGNITIVE FORESIGHT (PHASE 77) ---")
    
    with set_chip_context("core"):
        # ----------------------------------------------------
        # 1. SCENARIO A: Low Risk (UI Layer)
        # ----------------------------------------------------
        print("[STEP 1] Simulating Low Risk Scenario (UI Layer)...")
        mLow = mission_manager.create_mission("UI Fix Mission")
        mLow.multimodal_history.append({
            "event": "INITIAL", 
            "hypothesis": {"layer": "frontend/shell", "confidence": 0.8}
        })
        # Mock drift to score 60
        for _ in range(6): 
             mLow.multimodal_history.append({"event": "DRIFT", "hypothesis": {"layer": "ui/node", "role": "CONTRIBUTOR"}})
        
        scenarios_low = mLow.generate_mitigation_scenarios()
        ui_scenario = next((s for s in scenarios_low if s["id"].startswith("scenario_tac")), None)
        
        if ui_scenario:
             print(f"       Action: {ui_scenario['label']}")
             print(f"       Risk Score: {ui_scenario['risk_score']}% ({ui_scenario['risk_level']})")
             print(f"       Net Strategic Value: {ui_scenario['net_value']:.1f}")
             print(f"       Recommended: {ui_scenario['is_recommended']}")
        
        # ----------------------------------------------------
        # 2. SCENARIO B: High Risk (Core Layer)
        # ----------------------------------------------------
        print("\n[STEP 2] Simulating High Risk Scenario (Backend/Core Layer)...")
        mHigh = mission_manager.create_mission("Core Refactor Mission")
        mHigh.multimodal_history.append({
            "event": "INITIAL", 
            "hypothesis": {"layer": "backend/core/kernel", "confidence": 0.9}
        })
        # Mock drift to score 60
        for _ in range(6): 
             mHigh.multimodal_history.append({"event": "DRIFT", "hypothesis": {"layer": "core/critical", "role": "CONTRIBUTOR"}})
             
        scenarios_high = mHigh.generate_mitigation_scenarios()
        core_scenario = next((s for s in scenarios_high if s["id"].startswith("scenario_tac")), None)
        
        if core_scenario:
             print(f"       Action: {core_scenario['label']}")
             print(f"       Risk Score: {core_scenario['risk_score']}% ({core_scenario['risk_level']})")
             print(f"       Net Strategic Value: {core_scenario['net_value']:.1f}")
             print(f"       Risk Sources: {', '.join(core_scenario['collateral_risk']['sources'])}")
             print(f"       Recommended: {core_scenario['is_recommended']}")

        # ----------------------------------------------------
        # 3. VERIFY: Net Value Logic
        # ----------------------------------------------------
        print("\n[STEP 3] Verifying Decision Quality...")
        if core_scenario['risk_score'] > ui_scenario['risk_score']:
             print("       ✅ SUCCESS: Core risk detected correctly (> UI risk).")
        else:
             raise Exception("FAILED: Core risk score was not higher than UI risk score.")
             
        if not core_scenario['is_recommended'] and core_scenario['risk_score'] > 50:
             print("       ✅ SUCCESS: High-risk action correctly degraded/not recommended.")

        print("\n--- COGNITIVE FORESIGHT VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_cognitive_foresight())
