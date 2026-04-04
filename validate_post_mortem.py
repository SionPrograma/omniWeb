import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor

async def validate_post_mortem():
    print("--- VALIDATING STRATEGIC POST-MORTEM & KNOWLEDGE SYNTHESIS ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 1. SETUP: Create mission with proven rescue
        print("\n[STEP 1] Generating Proven Rescue Scenario...")
        m = mission_manager.create_mission("Post-Mortem Test Mission")
        await processor.process("[VISUAL_EVIDENCE] Phase 1", context={})
        m.multimodal_history[0]["hypothesis"] = {"layer": "backend/auth", "description": "Auth baseline"}
        
        # Add drift
        await processor.process("[VISUAL_EVIDENCE] Drift to CSS", context={})
        m.multimodal_history[-1]["hypothesis"] = {"layer": "frontend/css", "description": "CSS deviation"}
        mission_manager.save_mission(m)
        
        # Execute successful rescue
        # Ensure ROI is positive (score was 40, now it's 0 after focus restore)
        action = {"type": "RESTORE_FOCUS", "label": "Restore Auth Focus"}
        m.execute_realignment_action(action)
        mission_manager.save_mission(m)

        # 2. GENERATE HANDOFF (Includes Post-Mortem Synthesis)
        print("\n[STEP 2] Generating Handoff with Post-Mortem Synthesis...")
        handoff = m.generate_handoff()
        md = handoff.to_markdown()
        
        # 3. VERIFY SYNTHESIS
        print("\n[STEP 3] Verifying Markdown output and lessons...")
        if "🧠 Strategic Post-Mortem & Lessons Learned" not in md:
             raise Exception("FAILED: Strategic Post-Mortem section missing in handoff.")
             
        if "Lección Reutilizable:" not in md:
             raise Exception("FAILED: Reusable lesson missing in post-mortem.")
             
        if "backend/auth" not in md:
             raise Exception("FAILED: Domain context missing in distilled lesson.")

        print("\n--- POST-MORTEM FRAGMENT (PREVIEW) ---")
        pm_start = md.find("## 🧠 Strategic Post-Mortem")
        pm_end = md.find("## ⚖️ Key Decisions")
        print(md[pm_start:pm_end])

        print("\n--- STRATEGIC POST-MORTEM VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_post_mortem())
