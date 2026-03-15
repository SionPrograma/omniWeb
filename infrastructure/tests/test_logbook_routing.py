
import asyncio
import json
from backend.core.ai_host.command_router import ai_command_router
from backend.core.master_logbook.manager import master_logbook_manager
from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

async def test_routing():
    print("Initializing Database...")
    with set_chip_context("core"):
        db_manager.init_db()
        db_manager.run_migrations()

    print("\nTesting AI Host Routing to Master Logbook...")
    
    test_commands = [
        "Log an idea: add dark mode to delivery chip",
        "Create a task: audit semantic layer",
        "Fix: review shell navigation bug",
        "Analyze architecture: shell to AI Host flow"
    ]
    
    with set_chip_context("core"):
        for cmd in test_commands:
            print(f"\nProcessing: '{cmd}'")
            response = await ai_command_router.route(cmd)
            print(f"Intent: {response.intent}")
            print(f"Message: {response.message}")
            print(f"Status: {response.status}")
        
        print("\nVerifying Logbook Entries...")
        entries = master_logbook_manager.get_entries(limit=5)
        for e in entries:
            print(f"[{e.type}] {e.content} (Priority: {e.priority})")

if __name__ == "__main__":
    asyncio.run(test_routing())
