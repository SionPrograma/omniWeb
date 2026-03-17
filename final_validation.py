import asyncio
import sys
import os
from unittest.mock import MagicMock

# Add current dir to path
sys.path.append(os.getcwd())

from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.ai_host.processors.base import AICommandResponse

async def run_validation():
    print("\n=== STARTING FINAL VALIDATION ===\n")
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    orch = CognitiveOrchestrator(None)
    
    from backend.core.ai_host.sessions import session_state
    session_state.language = "es"

    # Testing Empty/Fallback Logic
    print("Testing Empty/Fallback Logic:")
    empty_input = ""
    
    for i in range(5):
        # Unify handles empty text
        mock_state = type('obj', (object,), {'health': type('obj', (object,), {'value': 'healthy'})})
        result = orch._unify_response(
            text=empty_input,
            system_state=mock_state,
            mode="direct_response",
            recent_context=[],
            intent_group="TEST"
        )
        print(f"Run {i+1}: {result}")
    print("")

    # Testing English Fallback
    print("Testing English Fallback Logic:")
    session_state.language = "en"
    for i in range(3):
        result = orch._unify_response(
            text=empty_input,
            system_state=mock_state,
            mode="direct_response",
            recent_context=[],
            intent_group="TEST"
        )
        print(f"Run {i+1}: {result}")
    print("")

    # Testing English
    print("Testing English Imperfection Layer:")
    session_state.language = "en"
    test_input_en = "There is a problem in internal communication. Everything is nominal for now. I'll check this layer."
    
    for i in range(5):
        result = orch._naturalize(test_input_en)
        final_result = orch._inject_human_imperfection(result)
        print(f"Run {i+1}: {final_result}")
    print("")

    print("=== VALIDATION COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_validation())
