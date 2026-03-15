
import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.getcwd())

from backend.core.ai_host.command_router import ai_command_router
from backend.core.ai_host.intent_classifier import intent_classifier

async def test_intents():
    test_cases = [
        ("open lingua", "open_chip"),
        ("show system state", "show_system_status"),
        ("log bug shell flicker", "log_entry"),
        ("launch translation", "launch_pipeline"),
        ("muestrame el logbook", "show_logbook"),
        ("como va el sistema", "show_system_status"),
        ("ejecutar flujo de traduccion", "launch_pipeline"),
        ("anota una idea para el shell", "log_entry")
    ]
    
    print("--- Testing Intent Classification ---")
    for msg, expected in test_cases:
        detected = intent_classifier.classify(msg)
        status = "✅" if detected == expected else f"❌ (Got {detected})"
        print(f"Msg: '{msg}' -> Intent: {detected} {status}")

async def test_routing():
    print("\n--- Testing Command Routing ---")
    commands = [
        "open lingua",
        "show system status",
        "log idea improve ai host",
        "launch pipeline"
    ]
    
    for cmd in commands:
        print(f"\nRouting: '{cmd}'")
        res = await ai_command_router.route(cmd)
        print(f"Intent: {res.intent}")
        print(f"Status: {res.status}")
        print(f"Message: {res.message[:100]}...")
        if res.payload:
            print(f"Payload: {list(res.payload.keys())}")

if __name__ == "__main__":
    asyncio.run(test_intents())
    asyncio.run(test_routing())
