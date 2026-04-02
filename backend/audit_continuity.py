import asyncio
import sys
import os

# Mock the backend environment
sys.path.append(os.getcwd())

from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
from backend.core.ai_host.routing.command_router import CommandRouter
from backend.core.ai_host.intent_understanding.conversation_tracker import conversation_tracker

async def audit_continuity():
    router = CommandRouter()
    session_id = "audit_session_1"
    
    print("\n--- AUDITING OMNI CONTINUITY ---\n")
    
    test_flows = [
        [
            "Hola Omni, ¿qué podés decirme del chip de finanzas?",
            "¿Por qué?",
            "Explicámelo mejor"
        ],
        [
            "Hay un problema de latencia en el backend.",
            "¿Cómo así?",
            "¿Y ahora?"
        ],
        [
            "Miremos el logbook.",
            "¿Qué ves en eso?",
            "Seguí"
        ]
    ]

    for flow in test_flows:
        print(f"FLOW START: {flow[0]}")
        # Reset session context for each flow simulation
        conversation_tracker.sessions[session_id] = conversation_tracker.get_context(session_id)
        conversation_tracker.sessions[session_id].history = []
        
        for msg in flow:
            print(f"\nUSER: {msg}")
            response = await router.route(msg, context={"user_id": session_id})
            print(f"OMNI: {response.message}")
            # Simulate state update if needed, though router.route calls update_context
        
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    asyncio.run(audit_continuity())
