import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager
from backend.core.ai_host.governance.drift_detector import drift_detector

async def validate_governance_hardening():
    print("--- VALIDATING MISSION GOVERNANCE HARDENING (PHASE 80) ---")
    
    with set_chip_context("core"):
        # 1. Create a mission and set a frozen layer
        m = mission_manager.create_mission("Governance Lock Validation")
        m.parameters["frozen_layers"] = ["backend/core"] # We freeze the core
        
        # Simulate that current focus is already in backend/core
        m.multimodal_history.append({
            "timestamp": "2026-04-03T00:00:00",
            "event": "INITIAL_CAPTURE",
            "hypothesis": {"layer": "backend/core/kernel", "description": "Analyzing kernel hooks."}
        })

        print("\n[STEP 1] Freeze Integrity Validation:")
        # Attempt an auto-recovery on a frozen layer context
        scenario = {
            "action": "RESTORE_EXECUTION_CONTEXT",
            "label": "Restore Kernel Context",
            "confidence": 0.99,
            "risk_score": 5
        }
        
        policy = m.evaluate_recovery_auto_policy(scenario)
        print(f"       Layer: backend/core/kernel (FROZEN)")
        print(f"       Policy Approval: {policy.get('allow_auto')}")
        print(f"       Policy Level: {policy.get('level')}")
        print(f"       Governance Reason: {policy.get('reason')}")
        
        if not policy.get('allow_auto') and "BLOQUEO CONSTITUCIONAL" in policy.get('reason', ''):
             print("       ✅ SUCCESS: Freeze Integrity Enforced. Recovery blocked.")
        else:
             print("       ❌ FAILURE: Freeze bypass detected in recovery engine.")

        print("\n[STEP 2] Drift Synchronization Validation:")
        # 2. Simulate high tactical drift and check for global alert
        m.multimodal_history.append({
            "timestamp": "2026-04-03T00:10:00",
            "event": "RE_ORIENTATION",
            "hypothesis": {"layer": "frontend/styles/main.css", "description": "Checking CSS variables?"}
        })
        
        # Clear existing alerts
        m.context_snap["drift_alerts"] = []
        
        print("       Triggering analyze_cognitive_drift()...")
        drift_report = m.analyze_cognitive_drift()
        print(f"       Tactical Drift Score: {drift_report['drift_score']}")
        
        # Check mission context_snap for the alerts recorded
        alerts = m.context_snap.get("drift_alerts", [])
        sync_found = any("Deriva cognitiva en aumento" in a.get("message", "") for a in alerts)
        
        if sync_found:
             print(f"       ✅ SUCCESS: Tactical drift synchronized with Global DriftDetector.")
             print(f"       Total Global Alerts recorded: {len(alerts)}")
             for a in alerts:
                  print(f"       - [{a.get('type')}] {a.get('message')}")
        else:
             print("       ❌ FAILURE: Global sync alert not found in mission context.")

    print("\n--- GOVERNANCE HARDENING VALIDATION FINISHED ---")

if __name__ == "__main__":
    asyncio.run(validate_governance_hardening())
