import asyncio
import sys
import os
import json

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), ".."))

# FIX: Force set DATA_DIR to absolute path before any other imports
from backend.core.config import settings
settings.DATA_DIR = os.path.join(os.getcwd(), "data")
print(f"DEBUG: Using DB at {settings.DATABASE_URL}")

# Mocking logging to avoid clutter
import logging
logging.basicConfig(level=logging.INFO)

async def test_evolution_report():
    from backend.core.ai_host import ai_command_router
    from backend.core.ai_host.monitoring.project_watcher import project_watcher
    from backend.core.ai_host.memory.project_manager import project_manager
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    
    # 1. Ensure we are in the right context
    with set_chip_context("core"):
        # 2. Simulate User Request
        print("\n--- TEST: Evolution Report Request ---")
        message = "Omni, haceme un reporte técnico del avance en logística."
        response = await ai_command_router.route(message)
        
        print(f"Intent: {response.intent}")
        print(f"Status: {response.status}")
        print(f"Message:\n{response.message}")
        
        if response.status == "success":
            report = response.payload.get("report")
            print(f"\nReport ID: {report['id']}")
            print(f"Project Slug: {report['project_slug']}")
            
        # 3. Simulate another request (Activity)
        print("\n--- TEST: Project Activity Request ---")
        message = "qué cambió desde que inicializamos el proyecto de logística"
        response = await ai_command_router.route(message)
        print(f"Intent: {response.intent}")
        print(f"Message:\n{response.message}")

if __name__ == "__main__":
    asyncio.run(test_evolution_report())
