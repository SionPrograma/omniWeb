
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

from backend.core.ai_host.command_router import ai_command_router
from backend.core.ai_host.memory.cluster_manager import cluster_manager

async def test_memory_routing_full():
    print("=== OMNIWEB — MEMORY ROUTING TEST (CLUSTERS) ===")
    
    # 1. Run grouping first to ensure clusters exist
    cluster_manager.auto_group_ideas()
    
    commands = [
        "Omni, listá mis clusters",
        "Omni, mostrá el cluster de logística",
        "Omni, agrupá mis ideas"
    ]
    
    for cmd in commands:
        print(f"\nCommand: {cmd}")
        response = await ai_command_router.route(cmd)
        print(f"Status: {response.status}")
        print(f"Intent: {response.intent}")
        print(f"Message: {response.message}")

if __name__ == "__main__":
    asyncio.run(test_memory_routing_full())
