import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager

async def validate_preventive_wisdom():
    print("--- VALIDATING STRATEGIC KNOWLEDGE INJECTION (PHASE 70) ---")
    
    with set_chip_context("core"):
        # 1. SETUP: Record a successful rescue lesson from the past
        print("\n[STEP 1] Recording Historical Strategic Success in 'backend/auth'...")
        # Pattern: backend/auth:ATTENTION_REQUIRED -> RESTORE_FOCUS
        mission_manager.learning_engine.record_rescue_success(
            context_key="backend/auth:ATTENTION_REQUIRED",
            action_type="RESTORE_FOCUS",
            roi=45.0
        )
        # Add another case to increase count and cases
        mission_manager.learning_engine.record_rescue_success(
            context_key="backend/auth:ATTENTION_REQUIRED",
            action_type="RESTORE_FOCUS",
            roi=55.0
        )

        # 2. CREATE NEW MISSION: Same Target Domain
        print("\n[STEP 2] Initializing New Mission in 'backend/auth'...")
        m = mission_manager.create_mission("New Auth Mission")
        # Add initial focus evidence
        m.multimodal_history.append({
            "event": "INITIAL_CAPTURE",
            "hypothesis": {"layer": "backend/auth", "description": "Auth layer initialization"},
            "timestamp": "2026-04-03T10:00:00Z"
        })
        mission_manager.save_mission(m)

        # 3. GENERATE PREVENTIVE BRIEFING
        print("\n[STEP 3] Generating Preventive Strategic Briefing...")
        briefing = m.generate_pre_mission_briefing()
        
        # 4. VERIFY WISDOM INJECTION
        print("\n[STEP 4] Verifying Wisdom Injection...")
        if briefing["status"] != "WISDOM_INJECTED":
             raise Exception(f"FAILED: Expected status WISDOM_INJECTED, got {briefing['status']}")
             
        if briefing["target_layer"] != "backend/auth":
             raise Exception(f"FAILED: Targeted wrong layer: {briefing['target_layer']}")
             
        found_lesson = False
        for l in briefing["lessons"]:
             if "RESTORE_FOCUS" in l["recommendation"] and "backend/auth" in l["context"]:
                  found_lesson = True
                  print(f"       ✅ Wisdom Found: {l['warning']}")
                  print(f"       ✅ Recommended Tactic: {l['recommendation']}")
                  
        if not found_lesson:
             raise Exception("FAILED: Specific historical lesson not injected in briefing.")

        print("\n--- BRIEFING MARKDOWN (PREVIEW) ---")
        print(briefing["briefing_markdown"])

        print("\n--- PREVENTIVE WISDOM VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_preventive_wisdom())
