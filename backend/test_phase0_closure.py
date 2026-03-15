import asyncio
import json
import os
import sys

# DEBUG
print("PYTHON STARTING", sys.version)
print("PYTHONPATH", os.environ.get("PYTHONPATH"))

from backend.core.ai_host.command_router import CommandRouter

async def test_closure():
    print("INITIALIZING COMMAND ROUTER...")
    router = CommandRouter()
    print("COMMAND ROUTER INITIALIZED.")
    
    tests = [
        ("hola", "EXPECTED: Greeting in Spanish (default)"),
        ("responde en inglés", "EXPECTED: Language set to English"),
        ("hi", "EXPECTED: Greeting in English"),
        ("diagnostic", "EXPECTED: Technical Diagnostic in English"),
        ("responde en español", "EXPECTED: Language set to Spanish"),
        ("analiza el sistema", "EXPECTED: System analysis in Spanish"),
        ("inspecciona el estado", "EXPECTED: System state in Spanish"),
        ("arregla el chat", "EXPECTED: UI repair in Spanish"),
        ("fix the chat", "EXPECTED: UI repair in Spanish (persisted lang)")
    ]
    
    context = {"user_id": "creator_test", "username": "creator"}
    
    print("=== FINAL PHASE 0 TEST CYCLE ===\n")
    
    for cmd, expected in tests:
        print(f"INPUT: {cmd}")
        res = await router.route(cmd, context=context)
        print(f"ROUTER: Routed to logic")
        print(f"INTENT: {res.intent}")
        print(f"MESSAGE: {res.message}")
        print("-" * 30)

if __name__ == "__main__":
    asyncio.run(test_closure())
