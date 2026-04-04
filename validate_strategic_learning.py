import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor

async def validate_strategic_learning():
    print("--- VALIDATING STRATEGIC EVOLUTION & LEARNING ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 1. SCENARIO 1: Create a mission and succeed in rescue
        print("\n[STEP 1] Generating Successful Past Rescue...")
        await processor.process("[VISUAL_EVIDENCE] Initial Auth", context={})
        m1 = mission_manager.get_active_mission()
        m1.multimodal_history[0]["hypothesis"] = {"layer": "auth", "description": "Auth focus"}
        
        # Add drift
        await processor.process("[VISUAL_EVIDENCE] Drift to CSS", context={})
        m1.multimodal_history[-1]["hypothesis"] = {"layer": "css", "description": "CSS noise"}
        mission_manager.save_mission(m1)
        
        # Execute successful rescue
        action = {"type": "RESTORE_FOCUS", "label": "Restore Auth"}
        # ROI is score_before - score_after. Let's force it.
        m1.execute_realignment_action(action)
        mission_manager.save_mission(m1)
        
        # 2. SCENARIO 2: Create a NEW SIMILAR mission
        print("\n[STEP 2] Creating New Similar Mission...")
        # (Using a new ID by clearing active focus in manager mock/impl if needed, 
        # or just starting new)
        m2 = mission_manager.create_mission("Second Auth Mission")
        await processor.process("[VISUAL_EVIDENCE] Initial Auth 2", context={})
        m2.multimodal_history[0]["hypothesis"] = {"layer": "auth", "description": "Auth focus"}
        
        # Add SAME drift
        await processor.process("[VISUAL_EVIDENCE] Drift to CSS 2", context={})
        m2.multimodal_history[-1]["hypothesis"] = {"layer": "css", "description": "CSS noise 2"}
        mission_manager.save_mission(m2)

        # 3. ANALYZE AND CHECK LEARNING ENRICHMENT
        print("\n[STEP 3] Analyzing new drift for historical support...")
        # Check database content directly to debug
        from backend.core.database import db_manager
        with db_manager.get_connection(internal=True) as conn:
             rows = conn.execute("SELECT * FROM mission_learning").fetchall()
             print(f"DEBUG DB Rows: {[dict(r) for r in rows]}")

        report = m2.analyze_cognitive_drift()
        suggestions = report["suggested_actions"]
        
        # Verify
        supported_action = next((s for s in suggestions if "Historial:" in s["label"]), None)
        
        if not supported_action:
             print("Dumping suggestions:", suggestions)
             raise Exception("FAILED: No historical support found in suggestions label.")
             
        print(f"ENRICHED SUGGESTION FOUND: {supported_action['label']}")
        print(f"Confidence: {supported_action.get('history_confidence')}")
        print(f"Cases: {supported_action.get('history_cases')}")

        if supported_action.get("history_cases", 0) < 1:
             raise Exception("FAILED: history_cases Count is incorrect.")

        print("\n--- STRATEGIC EVOLUTION & LEARNING VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_strategic_learning())
