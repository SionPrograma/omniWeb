
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
from backend.core.ai_host.processors.base import AICommandResponse
from backend.core.permissions import set_chip_context

async def run_policy_case(name, message, understanding):
    orchestrator = CognitiveOrchestrator()
    print(f"\n{'='*10} POLICY TEST: {name} {'='*10}")
    print(f"INPUT: {message}")
    
    with set_chip_context("core", user_id="1"):
        unified = await orchestrator.orchestrate(
            message=message,
            understanding=understanding,
            context={"user_id": "1"},
        )
    
    print("-" * 20)
    print("FINAL OUTPUT:\n", unified.message)
    print("-" * 20)
    return unified

async def main_policy_test():
    # 1. Low Risk - Memory
    await run_policy_case(
        "Low Risk (Memory Query)",
        "Qué recordás del roadmap?",
        {"mode": "direct_response", "intent_group": "MEMORY_INTENT"}
    )
    
    # 2. Medium Risk - Local Audit
    await run_policy_case(
        "Medium Risk (Local Audit)",
        "Auditá el archivo README.md",
        {"mode": "constrained_output", "intent_group": "COPILOT_PROPOSAL_INTENT"}
    )
    
    # 3. High Risk - Core Fix
    # Simulate a target_file in understanding context
    class MockContext:
        def __init__(self, target): self.target_file = target
    
    understanding_core = {
        "mode": "constrained_output", 
        "intent_group": "COPILOT_PROPOSAL_INTENT",
        "context": MockContext("backend/core/ai_host/orchestration/cognitive_orchestrator.py")
    }
    
    await run_policy_case(
        "High Risk (Core Microfix)",
        "Aplicá un fix en el orquestador core",
        understanding_core
    )

if __name__ == "__main__":
    asyncio.run(main_policy_test())
