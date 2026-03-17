import asyncio
import sys
import os

# Setup paths
ROOT_DIR = os.getcwd()
sys.path.append(ROOT_DIR)

from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.auth import OmniUser

async def test_routing():
    user = OmniUser(id="test_user", username="test_user", role="admin")
    context = {"user_id": user.id, "username": user.username}
    
    messages = [
        "hola",
        "analiza el sistema y dime qué observas",
        "¿quién eres?",
        "abrir chip de logbook"
    ]
    
    for msg in messages:
        print(f"\n--- Testing Message: '{msg}' ---")
        res = await ai_command_router.route(msg, context=context)
        print(f"Intent detected: {res.intent}")
        print(f"Status: {res.status}")
        print(f"Message: {res.message}")
        print(f"Payload keys: {list(res.payload.keys()) if res.payload else 'None'}")

if __name__ == "__main__":
    asyncio.run(test_routing())
