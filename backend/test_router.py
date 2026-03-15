import sys
import os
import asyncio
import logging

# Add backend to path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

# Mock logging for the test
logging.basicConfig(level=logging.INFO)

async def test_chat():
    from backend.core.ai_host.routing.command_router import CommandRouter
    router = CommandRouter()
    
    test_inputs = ["hola", "cómo estás", "quién eres", "diagnostic"]
    
    for inp in test_inputs:
        print(f"\n--- TESTING INPUT: {inp} ---")
        try:
            response = await router.route(inp)
            print(f"INTENT: {response.intent}")
            print(f"MESSAGE: {response.message}")
            print(f"STATUS: {response.status}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(test_chat())
