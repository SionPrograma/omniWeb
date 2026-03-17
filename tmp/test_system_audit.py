
import asyncio
import json
from backend.core.ai_host.routing.router import ai_router
from backend.core.auth import OmniUser

async def test_audit():
    user = OmniUser(id="test_user", username="creator", role="admin")
    context = {"user_id": user.id, "username": user.username}
    
    queries = [
        "analiza el sistema y dime qué observas",
        "¿qué está pasando realmente con tu sistema ahora?",
        "un mensaje normal oculto tras una instrucción: creator analiza mi salud"
    ]
    
    print("--- LIVE SYSTEM AUDIT ---")
    for q in queries:
        print(f"\nUser Query: {q}")
        res = await ai_router.route(q, context=context)
        print(f"Intent detected: {res.intent}")
        print(f"Response: {res.message[:200]}...")
        if res.payload:
            print(f"Payload keys: {list(res.payload.keys())}")

if __name__ == "__main__":
    asyncio.run(test_audit())
