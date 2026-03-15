import asyncio
import logging
import sys
import os

# Setup path
sys.path.append(os.getcwd())

# Configuration
from backend.core.permissions import set_chip_context
from backend.core.ai_host.execution.copilot_engine import copilot_engine

logging.basicConfig(level=logging.INFO)

async def audit_copilot_logic():
    print("=== OMNIWEB COPILOT AUDIT ===")
    
    # Needs core context for DB operations during execution
    with set_chip_context("core"):
        print("\n[STEP 1] Generating Plan...")
        prompt = "Create a new logistics optimization module"
        plan = await copilot_engine.generate_plan(prompt)
        
        print(f"Plan ID: {plan.id}")
        print(f"Steps count: {len(plan.steps)}")
        for i, s in enumerate(plan.steps):
            print(f"  {i+1}. {s.description} ({s.action_type})")
            
        print("\n[STEP 2] Executing Steps sequentially...")
        for step in plan.steps:
            print(f"Executing: {step.description}")
            result = await copilot_engine.execute_step(plan.id, step.id)
            if result.get("success"):
                print(f"  OK: {step.status}")
            else:
                print(f"  FAIL: {result}")
                break
                
        print("\n[STEP 3] Verifying Final Plan State...")
        if plan.status == "completed":
            print("Audit SUCCESS: Full plan executed.")
        else:
            print(f"Audit PENDING: Plan status is {plan.status}")

if __name__ == "__main__":
    asyncio.run(audit_copilot_logic())
