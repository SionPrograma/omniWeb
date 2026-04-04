import sys
import os
import asyncio
from datetime import datetime

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor

async def validate_drift_alerts():
    print("--- VALIDATING COGNITIVE DRIFT ALERTS ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 1. SETUP: Clean start for a new mission
        print("\n[STEP 1] Starting Fresh Mission...")
        await processor.process("[VISUAL_EVIDENCE] Initial setup", context={})
        m = mission_manager.get_active_mission()
        m.active_goal = "Build Secure API"
        m.multimodal_history[-1]["hypothesis"] = {"layer": "backend/api", "description": "API Focus"}
        mission_manager.save_mission(m)
        
        # 2. TRIGGER DRIFT (Become WARNING)
        print("\n[STEP 2] Adding Drift (Switch to UI styling)...")
        await processor.process("[VISUAL_EVIDENCE] CSS changes", context={})
        m.multimodal_history[-1]["hypothesis"] = {"layer": "frontend/ui", "description": "Styling colors"}
        mission_manager.save_mission(m)
        
        # 3. CHECK ALERT
        print("\n[STEP 3] Fetching Alerts...")
        alerts = mission_manager.get_drift_alerts()
        print(f"Alerts found: {len(alerts)}")
        if len(alerts) == 0:
             raise Exception("FAILED: Alert should have been triggered for DRIFT_WARNING.")
        
        # 4. CHECK ANTI-SPAM (Same state)
        print("\n[STEP 4] Fetching Alerts again (Expect 0 due to anti-spam)...")
        alerts2 = mission_manager.get_drift_alerts()
        print(f"Alerts found (2nd try): {len(alerts2)}")
        if len(alerts2) > 0:
             raise Exception("FAILED: Anti-spam failed. Repeated alert for same state.")

        # 5. TRIGGER CRITICAL DRIFT
        print("\n[STEP 5] Escalating to CRITICAL...")
        # Add memory noise
        m.reactivate_archival_snapshot(m.multimodal_history[0]["id"], active=True, reason="Drift")
        mission_manager.save_mission(m)
        
        alerts3 = mission_manager.get_drift_alerts()
        print(f"Alerts found (Critical escalation): {len(alerts3)}")
        if len(alerts3) == 0:
             raise Exception("FAILED: Should alert for escalation to CRITICAL_DRIFT.")

        print("\n--- COGNITIVE DRIFT ALERTS VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_drift_alerts())
