import asyncio
import sys
import os

# Set up path to include project root
sys.path.append(os.getcwd())

from backend.core.ai_host.execution.copilot_engine import copilot_engine

async def run_audit_validation():
    print("=== OMNIWEB COPILOT PHASE 2 VALIDATION ===")
    
    # 1. Test Audit System
    print("\n[STEP 1] Testing System Audit...")
    plan_audit = await copilot_engine.generate_plan("Auditá el sistema actual y mostrame los problemas.")
    print(f"Plan generated: {plan_audit.id}")
    for step in plan_audit.steps:
        print(f"Executing step: {step.description}")
        result = await copilot_engine.execute_step(plan_audit.id, step.id)
        if result['success']:
            print(f"Success: {result['message']}")
            print(f"Issues detected: {len(result.get('data', []))}")
        else:
            print(f"FAILED: {result.get('error')}")

    # 2. Test Proposal Generation
    print("\n[STEP 2] Testing Correction Proposal...")
    plan_proposal = await copilot_engine.generate_plan("Proponé corrección para el problema principal.")
    for step in plan_proposal.steps:
        result = await copilot_engine.execute_step(plan_proposal.id, step.id)
        if result['success']:
            print(f"Success: {result['message']}")
            print(f"Proposals generated: {len(result.get('data', []))}")
            for p in result['data']:
                print(f" - Proposal: {p['title']} (Risk: {p['risk_level']})")
        else:
            print(f"FAILED: {result.get('error')}")

    # 3. Test Patch Execution
    print("\n[STEP 3] Testing Patch Execution & Re-audit...")
    plan_patch = await copilot_engine.generate_plan("Aplicá la corrección aprobada.")
    for step in plan_patch.steps:
        result = await copilot_engine.execute_step(plan_patch.id, step.id)
        print(f"Step: {step.description} -> {'PASS' if result['success'] else 'FAIL'}")
        if result['success']:
            print(f"Result: {result['message']}")

    print("\n=== VALIDATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_audit_validation())
