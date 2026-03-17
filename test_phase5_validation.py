import asyncio
import sys
import os
import logging

# Setup paths
ROOT_DIR = os.getcwd()
sys.path.append(ROOT_DIR)

from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.auth import OmniUser
from backend.core.ai_host.memory.semantic_memory import semantic_memory

logging.basicConfig(level=logging.INFO)

async def test_validation():
    user = OmniUser(id="test_user", username="test_user", role="admin")
    context = {"user_id": user.id, "username": user.username}
    
    # Reset memory for clean test
    semantic_memory.clear()
    
    prompts = [
        "analiza el sistema y dime qué observas",
        "¿qué está pasando realmente con tu sistema ahora?",
        "te estuve probando hace un rato, ¿qué puedes inferir de eso?",
        "usa el contexto de esta conversación para responder mejor",
        "si tuvieras que mejorar tu arquitectura, ¿qué harías?"
    ]
    
    print("\n" + "="*50)
    print("PHASE 5: LIVE COGNITIVE VALIDATION")
    print("="*50)
    
    for i, msg in enumerate(prompts):
        print(f"\n[PROMPT {i+1}] {msg}")
        res = await ai_command_router.route(msg, context=context)
        print(f"--- RESPONSE ---")
        print(f"Intent: {res.intent}")
        print(f"Response: {res.message}")
        if res.payload:
            print(f"Payload keys: {list(res.payload.keys())}")
        print("-"*50)

if __name__ == "__main__":
    asyncio.run(test_validation())
