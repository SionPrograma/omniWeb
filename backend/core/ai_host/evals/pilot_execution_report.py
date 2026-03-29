
import asyncio
import sys
import os
import logging

# Add project root to sys.path
sys.path.append(os.getcwd())

from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
from backend.core.ai_host.processors.base import AICommandResponse
from backend.core.permissions import set_chip_context

async def run_pilot_case(name, message, understanding, context=None):
    orchestrator = CognitiveOrchestrator()
    print(f"\n{'='*10} PILOT CATEGORY: {name} {'='*10}")
    print(f"INPUT: {message}")
    
    with set_chip_context("core", user_id="1"):
        unified = await orchestrator.orchestrate(
            message=message,
            understanding=understanding,
            context=context or {"user_id": "1"},
        )
    
    print("-" * 20)
    print("COPILOT NORMALIZED OUTPUT:\n", unified.message)
    print("-" * 20)
    return unified

async def main_pilot():
    # Category 1: Surgical Microfix
    # Testing ProposalProcessor (Heuristics)
    await run_pilot_case(
        "1. SURGICAL MICROFIX (LOGIC)",
        "Aplicá un microfix en backend/core/ai_host/orchestration/cognitive_orchestrator.py para logging",
        {"mode": "constrained_output", "intent_group": "COPILOT_PROPOSAL_INTENT"}
    )
    
    # Category 2: Architectural Audit (Smells)
    await run_pilot_case(
        "2. ARCHITECTURAL AUDIT (SMELLS)",
        "Auditá el archivo backend/core/ai_host/brain_router.py",
        {"mode": "constrained_output", "intent_group": "COPILOT_PROPOSAL_INTENT"}
    )
    
    # Category 3: Global System Awareness (Impact)
    await run_pilot_case(
        "3. GLOBAL SYSTEM AWARENESS",
        "Analizá la arquitectura del sistema completo de OmniWeb",
        {"mode": "constrained_output", "intent_group": "COPILOT_PROPOSAL_INTENT"}
    )
    
    # Category 4: Operational Memory Retrieval
    await run_pilot_case(
        "4. OPERATIONAL MEMORY RETRIEVAL",
        "Qué recordás de las últimas decisiones del roadmap?",
        {"mode": "direct_response", "intent_group": "MEMORY_INTENT"}
    )

if __name__ == "__main__":
    asyncio.run(main_pilot())
