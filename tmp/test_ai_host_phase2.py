import asyncio
import sys
import os

# Update path to include backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Set mock env vars if needed
os.environ["DATABASE_URL"] = "sqlite:///test_omni.db"

from backend.core.ai_host.command_router import ai_command_router
from backend.core.master_logbook.manager import master_logbook_manager
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

async def test_intents():
    print("--- Testing Phase 2 Intents ---")
    
    with set_chip_context("core"):
        # Setup test DB
        db_manager.init_db()
        db_manager.run_migrations()
    
        test_commands = [
            "log bug shell flicker in development",
            "show recent bugs",
            "show system state",
            "open lingua",
            "launch translation"
        ]
        
        for cmd in test_commands:
            print(f"\nUser: {cmd}")
            res = await ai_command_router.route(cmd)
            print(f"AI (Intent: {res.intent}): {res.message}")
            if res.payload:
                print(f"Payload: {res.payload.keys()}")

        # Test confirmation flow
        print("\n--- Testing Confirmation Flow ---")
        cmd = "confirm launch translation"
        print(f"User: {cmd}")
        res = await ai_command_router.route(cmd)
        print(f"AI (Intent: {res.intent}): {res.message}")

if __name__ == "__main__":
    asyncio.run(test_intents())
