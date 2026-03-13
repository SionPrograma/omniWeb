import asyncio
import sys
import os
import json
import shutil

# Add project root to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.core.system_auditor.auditor import auditor
from backend.core.system_auditor.fix_engine import fix_engine
from backend.core.system_auditor.models import AuditStatus

async def test_healing_loop():
    print("🚀 Starting OmniWeb Self-Healing Loop Test (Phase 8)...")
    
    # SETUP: Create a "broken" chip
    chip_name = "chip-healing-loop-test"
    broken_chip_dir = f"chips/{chip_name}"
    os.makedirs(broken_chip_dir, exist_ok=True)
    manifest_path = os.path.join(broken_chip_dir, "chip.json")
    
    # Intentionally missing 'slug', 'name', and 'entry'
    broken_manifest = {
        "id": chip_name,
        "version": "0.1.0"
    }
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(broken_manifest, f)
        
    print(f"Created broken chip at {broken_chip_dir}")

    try:
        max_iterations = 4
        current_iteration = 0
        resolved = False

        while current_iteration < max_iterations:
            current_iteration += 1
            print(f"\n--- Healing Iteration {current_iteration} ---")
            
            # 1. AUDIT
            report = await auditor.run_full_audit()
            
            # Filter issues related to our test chip
            chip_issues = [i for i in report.issues if chip_name in i.message]
            
            if not chip_issues:
                print(f"✅ No more issues found for {chip_name}!")
                resolved = True
                break
                
            print(f"Detected {len(chip_issues)} issues for {chip_name}:")
            for i in chip_issues:
                print(f" - {i.message}")

            # 2. PROPOSE & APPLY
            # The Auditor already triggered fix_engine.analyze_report(report) internally
            fixes = [f for f in fix_engine.active_proposals.values() if any(chip_name in a.target or chip_name in f.issue_message for a in f.actions)]
            
            if not fixes:
                print("❌ No fixes proposed for detected issues.")
                break
                
            print(f"Applying fix: {fixes[0].id} ({fixes[0].analysis})")
            success = await fix_engine.apply_fix(fixes[0].id)
            
            if not success:
                print("❌ Fix application failed.")
                break
            
            # Clear proposal after apply (the engine should do this but let's be safe for the loop)
            if fixes[0].id in fix_engine.active_proposals:
                del fix_engine.active_proposals[fixes[0].id]

        if resolved:
             print("\n🎉 SELF-HEALING STABLE: System recovered automatically after multiple steps.")
        else:
             print("\n❌ SELF-HEALING FAILED: System could not reach stability.")

    finally:
        # Cleanup
        if os.path.exists(broken_chip_dir):
            shutil.rmtree(broken_chip_dir)
            print(f"\nCleaned up test chip: {broken_chip_dir}")

if __name__ == "__main__":
    asyncio.run(test_healing_loop())
