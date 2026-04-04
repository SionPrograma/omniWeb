import sys
import os
import asyncio
import json

# Set up backend path
sys.path.append(os.getcwd())

from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_manager import mission_manager

async def validate_constitution_audit():
    print("--- VALIDATING OMNIWEB CONSTITUTIONAL AUDIT ---")
    
    with set_chip_context("core"):
        # 1. Create a mission and simulate some state context
        m = mission_manager.create_mission("Audited Infrastructure Phase")
        
        # Scenario: Add a frozen layer to trigger a constitutional conflict detection
        m.parameters["frozen_layers"] = ["backend/core/kernel"]
        
        print("\n[STEP 1] Executing Constitutional Audit Engine...")
        report = m.perform_autonomy_audit()
        
        print("\n[STEP 2] Audit Result Summary:")
        print(f"       Status: {report['status']}")
        print(f"       Health Score: {report['health_score']:.2f}")
        
        print("\n[STEP 3] Inventory of Mapped Surfaces:")
        for s in report['inventory']['surfaces']:
             print(f"       - {s['name']}: {s['scope']} [{s['status']}]")

        print("\n[STEP 4] Decision Matrix Audit:")
        for level, actions in report['decision_matrix'].items():
             print(f"       - {level.upper()}: {', '.join(actions)}")

        print("\n[STEP 5] Gap Analysis (Issues Detected):")
        if report['detected_issues']:
             for issue in report['detected_issues']:
                  print(f"       - [!] {issue['finding']} (Surface: {issue['surface']})")
                  print(f"         RECOMMENDATION: {issue['recommendation']}")
        else:
             print("       No gaps detected.")

        # ----------------------------------------------------
        # VERIFICATION: Does the markdown output exist for UI?
        # ----------------------------------------------------
        print("\n[STEP 6] UI Traceability Check:")
        if "audit_markdown" in report:
             print("       ✅ Audit Markdown generated for Pizarrón Vivo.")
        
        # Consistency Check: Is the Sensitive Layer pinning rule functioning?
        print("\n[STEP 7] Governance Consistency Check (Sensitive Layer):")
        audit_res = m.evaluate_mitigation_autonomy("MUTATION", "backend/core/kernel", 0.99)
        print(f"       Action: MUTATION | Layer: backend/core/kernel")
        print(f"       Result Level: {audit_res['level']}")
        if audit_res['level'] == "PIN_REQUIRED":
              print("       ✅ SUCCESS: Strategic and Tactical layers are aligned on Core Sensitivity.")

    print("\n--- CONSTITUTIONAL AUDIT VALIDATION FINISHED ---")

if __name__ == "__main__":
    asyncio.run(validate_constitution_audit())
