import sys
import os
import json
import asyncio
from datetime import datetime

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager, MissionStatus
from backend.core.ai_host.processors.multimodal_processor import MultimodalProcessor

async def validate_portfolio_drift():
    print("--- VALIDATING PORTFOLIO COGNITIVE HEALTH ---")
    
    processor = MultimodalProcessor()
    
    with set_chip_context("core"):
        # 0. SETUP: Clear or isolate active (Optional depending on DB state)
        
        # MISSION A: ALIGNED (Backend focus)
        print("\n[MISSION A] Starting Aligned Mission: 'Task A'...")
        await processor.process("[VISUAL_EVIDENCE] Start A", context={})
        mA = mission_manager.get_active_mission()
        mA.active_goal = "Process Backend Data"
        mA.multimodal_history[-1]["hypothesis"] = {"layer": "backend/core", "description": "Processing..."}
        mission_manager.save_mission(mA)
        mission_manager.active_mission = None # Deselect to create new

        # MISSION B: CRITICAL DRIFT (Started as Auth, now CSS)
        print("\n[MISSION B] Starting Deviated Mission: 'Task B'...")
        await processor.process("[VISUAL_EVIDENCE] Start B (Auth)", context={})
        mB = mission_manager.get_active_mission()
        mB.active_goal = "Secure Login Endpoint"
        mB.multimodal_history[-1]["hypothesis"] = {"layer": "backend/auth", "description": "Auth init"}
        mission_manager.save_mission(mB)
        
        # Add deviation to B
        await processor.process("[VISUAL_EVIDENCE] UI Drift for B", context={})
        mB.multimodal_history[-1]["hypothesis"] = {"layer": "frontend/ui", "description": "Fixing colors"}
        # Add memory noise to B
        mB.reactivate_archival_snapshot(mB.multimodal_history[0]["id"], active=True, reason="Noise")
        mission_manager.save_mission(mB)
        mission_manager.active_mission = None

        # 1. ANALYZE PORTFOLIO
        print("\n[STEP 1] Fetching Portfolio Cognitive Health...")
        health = mission_manager.get_portfolio_cognitive_health()
        
        print(f"Missions analyzed: {len(health)}")
        
        # Verify Ranking (B should be first due to Critical/Warning status and higher score)
        if len(health) < 2:
             print("WARNING: Not enough missions to verify ranking.")
        else:
             top = health[0]
             print(f"TOP RISK: {top['mission_id']} | Goal: {top['goal']} | Score: {top['drift_score']}")
             if top['drift_score'] < 40:
                  raise Exception("FAILED: Mission B should have high drift score.")
             if "Task B" not in top['goal'] and "Login" not in top['goal']:
                  raise Exception("FAILED: Deviated mission should be at the top of the portfolio.")

        # 2. Verify Urgency
        criticals = [m for m in health if m['urgency'] == 'HIGH']
        print(f"High risk missions found: {len(criticals)}")
        
        print("\n--- PORTFOLIO DRIFT VALIDATION SUCCESSFUL ---")

if __name__ == "__main__":
    asyncio.run(validate_portfolio_drift())
