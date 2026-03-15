
import asyncio
import sys
import os
import importlib

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

from backend.core.permissions import set_chip_context
from backend.core.database import db_manager

async def test_persistence():
    print("--- Memory Persistence Bridge Test ---")
    
    # 1. Clear tables for clean test
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM ai_host_ideas")
            conn.execute("DELETE FROM ai_host_knowledge_nodes")
            conn.execute("DELETE FROM ai_host_knowledge_edges")
            conn.commit()
    print("Tables cleared.")

    # Import modules to get global instances
    import backend.core.ai_host.memory.knowledge_graph as kg_mod
    import backend.core.ai_host.memory.idea_capture as ic_mod
    
    # Reset in-memory state if already loaded
    kg_mod.knowledge_graph.nodes = {}
    ic_mod.idea_capture.ideas = {}

    # 2. Capture an idea
    test_text = "Idea de prueba: drones de reparto ultrarápidos."
    print(f"Capturing idea: '{test_text}'")
    idea = ic_mod.idea_capture.capture_idea(test_text)
    
    print(f"Idea memory count: {len(ic_mod.idea_capture.ideas)}")
    print(f"Knowledge Graph node count: {len(kg_mod.knowledge_graph.nodes)}")
    
    # 3. Simulate Restart by re-initializing handlers
    print("\n--- Simulating Restart (Re-initializing) ---")
    
    # We create NEW instances to see if they load from DB
    from backend.core.ai_host.memory.idea_capture import IdeaCapture
    from backend.core.ai_host.memory.knowledge_graph import KnowledgeGraph
    
    new_kg = KnowledgeGraph()
    new_ic = IdeaCapture()
    
    print(f"Reloaded Idea count: {len(new_ic.ideas)}")
    print(f"Reloaded Knowledge Node count: {len(new_kg.nodes)}")
    
    # 4. Verify content
    if len(new_ic.ideas) > 0:
        reloaded_idea = list(new_ic.ideas.values())[0]
        print(f"Reloaded content: '{reloaded_idea.content}'")
        if reloaded_idea.content == test_text:
            print("SUCCESS: Idea content matched.")
        else:
            print("FAILURE: Idea content mismatch.")
    else:
        print("FAILURE: No ideas reloaded.")

    # 5. Verify search
    search_results = new_kg.search_knowledge("reparto")
    print(f"Search results for 'reparto': {len(search_results)}")
    if len(search_results) > 0:
        print(f"Search result title: '{search_results[0].title}'")
        print("SUCCESS: Search works on reloaded state.")
    else:
        print("FAILURE: Search failed on reloaded state.")

if __name__ == "__main__":
    asyncio.run(test_persistence())
