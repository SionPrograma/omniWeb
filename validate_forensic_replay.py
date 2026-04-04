import sys
import os
import asyncio
from datetime import datetime

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager

async def validate_forensic_replay():
    print("--- VALIDATING COGNITIVE FORENSIC REPLAY (PHASE 71) ---")
    
    with set_chip_context("core"):
        # 1. SETUP: Create complex mission history
        print("\n[STEP 1] Generating Complex Mission History...")
        m = mission_manager.create_mission("Forensic Replay Test")
        
        # Step A: Initialization
        m.multimodal_history.append({
            "event": "INITIAL_CAPTURE",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": {"layer": "frontend", "description": "Analyzing UI responsiveness"},
            "relevance": "CRITICAL"
        })
        
        # Step B: Drift toward Backend
        m.multimodal_history.append({
            "event": "RE_ORIENTATION",
            "timestamp": datetime.now().isoformat(),
            "hypothesis": {"layer": "backend", "description": "Suspicion of slow API response"},
            "relevance": "SIGNAL"
        })
        
        # Step C: Rescue (Realignment)
        m.multimodal_history.append({
            "event": "REALIGNMENT_ROI",
            "timestamp": datetime.now().isoformat(),
            "performance": {
                "action": "RESTORE_UI_SCOPE",
                "layer_before": "backend",
                "layer_after": "frontend",
                "roi": 85.0
            },
            "relevance": "CRITICAL"
        })
        
        mission_manager.save_mission(m)
        print(f"       ✅ Mission created with {len(m.multimodal_history)} evolutionary steps.")

        # 2. GENERATE REPLAY TRACE
        print("\n[STEP 2] Reconstructing Forensic Trace...")
        trace = m.generate_cognitive_replay_trace()
        
        # 3. VERIFY TRACE INTEGRITY
        print("\n[STEP 3] Verifying Trace Integrity...")
        if len(trace) != 3:
             raise Exception(f"FAILED: Expected 3 trace steps, got {len(trace)}")
             
        # Verify Step 1: Initial Focus
        if trace[0]["current_focus"] != "frontend" or trace[0]["event"] != "🎯 TARGET INITIALIZATION":
             raise Exception(f"FAILED Step 1: Wrong focus or event: {trace[0]}")
        print("       ✅ Step 1 (Init): Verified.")

        # Verify Step 2: Target Shift (Drift)
        if trace[1]["current_focus"] != "backend" or trace[1]["event"] != "🔄 RE-ORIENTATION":
             raise Exception(f"FAILED Step 2: Fails to capture shift: {trace[1]}")
        print("       ✅ Step 2 (Shift): Verified.")

        # Verify Step 3: Rescue Recovery
        if trace[2]["current_focus"] != "frontend" or "RESCUE" not in trace[2]["event"]:
             raise Exception(f"FAILED Step 3: Fails to capture recovery: {trace[2]}")
        print("       ✅ Step 3 (Rescue): Verified.")

        # 4. PRINT PREVIEW
        print("\n--- FORENSIC REPLAY DATA (PREVIEW) ---")
        for t in trace:
             print(f"Step {t['step']}: {t['event']} | Focus: {t['current_focus']} | Desc: {t['description'][:40]}...")

        print("\n--- COGNITIVE REPLAY VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_forensic_replay())
