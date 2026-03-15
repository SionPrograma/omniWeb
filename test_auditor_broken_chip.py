import os
import sys
import json
import asyncio
from fastapi import FastAPI

# Setup broken chip
CHIPS_DIR = "chips"
BROKEN_CHIP_DIR = os.path.join(CHIPS_DIR, "chip-audit_test")

def setup_broken_chip():
    os.makedirs(os.path.join(BROKEN_CHIP_DIR, "core"), exist_ok=True)
    with open(os.path.join(BROKEN_CHIP_DIR, "chip.json"), "w") as f:
        json.dump({
            "id": "chip-audit_test",
            "slug": "audit_test",
            "name": "Audit Test Chip",
            "has_backend": True,
            "active": True
        }, f)
    with open(os.path.join(BROKEN_CHIP_DIR, "core", "router.py"), "w") as f:
        f.write("raise RuntimeError('Intended Test Crash')")

async def run_audit():
    sys.path.append(os.getcwd())
    from backend.core.module_registry import module_registry
    from backend.core.system_auditor.auditor import auditor
    app = FastAPI()
    
    # 1. Simulate registration
    try:
        module_registry.register_module(app, "audit_test", "chips.chip-audit_test.core.router")
    except Exception as e:
        # Prev turning patch
        module_registry._register_module_state("audit_test", None, {"slug": "audit_test", "has_backend": True, "active": True})
    
    # 2. Run Audit
    print("\n--- RUNNING AUDIT ---")
    report = await auditor.run_full_audit()
    
    found = False
    for issue in report.issues:
        print(f"[{issue.sector.value}] {issue.level.value}: {issue.message}")
        if "audit_test" in issue.message:
            found = True
            
    if not found:
        print("\nRESULT: Mismatch! Auditor did NOT detect the failed backend for 'audit_test'.")
    else:
        print("\nRESULT: Auditor detected the issue.")

if __name__ == "__main__":
    try:
        setup_broken_chip()
        asyncio.run(run_audit())
    finally:
        if os.path.exists(BROKEN_CHIP_DIR):
            import shutil
            shutil.rmtree(BROKEN_CHIP_DIR)
