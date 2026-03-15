import asyncio
import sys
import os

sys.path.append(os.getcwd())

from backend.core.ai_host.execution.copilot_engine import copilot_engine

async def run_chip_validation():
    print("=== OMNIWEB COPILOT CHIP AUDIT VALIDATION ===")
    
    # Test Audit Chip Reparto
    print("\n[STEP 1] Testing Chip Audit (Reparto)...")
    plan_chip = await copilot_engine.generate_plan("Auditá el chip Reparto y decime qué corregirías.")
    for step in plan_chip.steps:
        result = await copilot_engine.execute_step(plan_chip.id, step.id)
        if result['success']:
            print(f"Success: {result['message']}")
            print(f"Issues detected: {len(result.get('data', []))}")
            for issue in result.get('data', []):
                print(f" - Issue: {issue['title']} (Layer: {issue['layer']})")
        else:
            print(f"FAILED: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(run_chip_validation())
