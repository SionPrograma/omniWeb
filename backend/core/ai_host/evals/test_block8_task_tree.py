
import asyncio
import sys
import os

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
from backend.core.ai_host.processors.base import AICommandResponse
from backend.core.permissions import set_chip_context

async def run_task_tree_case(name, message):
    orchestrator = CognitiveOrchestrator()
    print(f"\n{'='*10} TASK TREE TEST: {name} {'='*10}")
    print(f"INPUT: {message}")
    
    with set_chip_context("core", user_id="1"):
        unified = await orchestrator.orchestrate(
            message=message,
            understanding={"mode": "reflective_analysis", "intent_group": "COPILOT_PROPOSAL_INTENT"},
            context={"user_id": "1"},
        )
    
    print("-" * 20)
    print("FINAL OUTPUT:\n", unified.message)
    print("-" * 20)
    return unified

async def main_tree_test():
    # 1. Frontend Workspace Task
    await run_task_tree_case(
        "Workspace Mission",
        "Mejorá el color de fondo del workspace de OmniWeb"
    )
    
    # 2. Memory Task
    await run_task_tree_case(
        "Memory Mission",
        "Auditá la memoria semántica y buscá inconsistencias"
    )
    
    # 3. Copilot Task
    await run_task_tree_case(
        "Copilot Mission",
        "Refactorizá el normalizador del copiloto"
    )

if __name__ == "__main__":
    asyncio.run(main_tree_test())
