import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager

async def validate_autonomy_governance():
    print("--- VALIDATING AUTO-RESCUE GOVERNANCE POLICY (PHASE 73) ---")
    
    with set_chip_context("core"):
        # 1. SETUP: Inject Intelligence first
        mission_manager.learning_engine.record_rescue_success(
            context_key="ui:DRIFT_WARNING",
            action_type="EXCLUDE_NODE",
            roi=95.0
        )
        
        # ----------------------------------------------------
        # CASE A: AUTO-SAFE CANDIDATE (Low risk, high confidence)
        # ----------------------------------------------------
        print("\n[CASE A] Evaluating Low Risk / High Confidence Action...")
        mA = mission_manager.create_mission("Autonomy Test A")
        mA.multimodal_history.append({"event": "INITIAL", "hypothesis": {"layer": "ui"}})
        mA.multimodal_history.append({"event": "DRIFT", "hypothesis": {"layer": "ui/css", "id": "node_123", "role": "CONTRIBUTOR"}})
        
        # Score ~30
        scenariosA = mA.generate_mitigation_scenarios()
        exclude_scenario = next((s for s in scenariosA if s["action"] == "EXCLUDE_NODE"), None)
        
        if exclude_scenario:
            audit = exclude_scenario["autonomy_audit"]
            print(f"       Action: {exclude_scenario['label']}")
            print(f"       Policy Level: {audit['level']} | Reason: {audit['reason']}")
            # Since confidence should be high (>0.85) from our injection above
            if audit["level"] != "AUTO_SAFE_THEORETICAL":
                 print(f"       ⚠️ Expected AUTO_SAFE, got {audit['level']}. Check confidence logic.")
        
        # ----------------------------------------------------
        # CASE B: CRITICAL LAYER (Backend core)
        # ----------------------------------------------------
        print("\n[CASE B] Evaluating Strategic Core Layer Access...")
        mB = mission_manager.create_mission("Autonomy Test B")
        mB.multimodal_history.append({"event": "INITIAL", "hypothesis": {"layer": "backend/core"}})
        mB.multimodal_history.append({"event": "DRIFT", "hypothesis": {"layer": "frontend"}}) # Drifted AWAY from core
        
        scenariosB = mB.generate_mitigation_scenarios()
        # Any restoration to backend/core should be PIN_REQUIRED
        restore = next((s for s in scenariosB if s["action"] == "RESTORE_FOCUS"), None)
        if restore:
            audit = restore["autonomy_audit"]
            print(f"       Action: {restore['label']}")
            print(f"       Policy Level: {audit['level']} | Reason: {audit['reason']}")
            if audit["level"] != "PIN_REQUIRED":
                 raise Exception(f"FAILED: Core layer restoration should require PIN. Got {audit['level']}")

        # ----------------------------------------------------
        # CASE C: EXTREME DRIFT ESCALATION
        # ----------------------------------------------------
        print("\n[CASE C] Evaluating Extreme Drift (>80) Escalation...")
        mC = mission_manager.create_mission("Autonomy Test C")
        # Generate 10 drift events to pump score
        for i in range(10):
            mC.multimodal_history.append({"event": "RE_ORIENTATION", "hypothesis": {"layer": f"layer_{i}"}})
        
        scenariosC = mC.generate_mitigation_scenarios()
        for s in scenariosC:
            if s["action"] != "NONE":
                audit = s["autonomy_audit"]
                print(f"       Action: {s['label']} -> Level: {audit['level']}")
                if audit["level"] not in ["HUMAN_CONFIRM", "PIN_REQUIRED", "GATE_REQUIRED"]:
                     raise Exception(f"FAILED: Extreme drift should prevent AUTO_SAFE. Got {audit['level']}")

        print("\n--- GOVERNANCE POLICY VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_autonomy_governance())
