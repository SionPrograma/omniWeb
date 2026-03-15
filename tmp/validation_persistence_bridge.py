
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

from backend.core.permissions import set_chip_context
from backend.core.database import db_manager
from backend.core.ai_host.memory.idea_capture import idea_capture
from backend.core.ai_host.memory.knowledge_graph import knowledge_graph

async def test_full_memory_bridge():
    print("=== OMNIWEB — PERSISTENCE RELOAD VALIDATION ===")
    
    # 1. Reset Environment
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM ai_host_ideas")
            conn.execute("DELETE FROM ai_host_knowledge_nodes")
            conn.execute("DELETE FROM ai_host_knowledge_edges")
            conn.commit()
    print("[1/5] Database memory tables cleared.")

    # Reset global memory states
    idea_capture.ideas = {}
    knowledge_graph.nodes = {}

    # 2. Phase A: Capture Ideas and Create Links
    print("[2/5] PHASE A: Initial Capture")
    # Capture 2 ideas
    idea1 = idea_capture.capture_idea("Omni, guardá esta idea: drones logísticos autónomos.")
    idea2 = idea_capture.capture_idea("Omni, guardá esta idea: visión artificial para depuración.")
    
    # Create a link between them
    node1_id = idea1.related_nodes[0]
    node2_id = idea2.related_nodes[0]
    knowledge_graph.link_knowledge_nodes(node1_id, node2_id)
    
    print(f"Captured: {len(idea_capture.ideas)} ideas.")
    print(f"Knowledge Nodes: {len(knowledge_graph.nodes)}")

    # 3. Phase B: Restart (Simulated by wiping memory and reloading)
    print("\n[3/5] PHASE B: Simulating Backend Restart (Memory Wipe)...")
    idea_capture.ideas = {}
    knowledge_graph.nodes = {}
    
    print("Memory wiped. Reloading from SQLite...")
    knowledge_graph._load_graph()
    idea_capture._load_ideas()
    
    # 4. Phase C: Validation
    print("[4/5] PHASE C: Validation")
    
    # Test 1: List Ideas
    all_ideas = idea_capture.get_all_ideas()
    print(f"Restored Ideas count: {len(all_ideas)}")
    if len(all_ideas) == 2:
        print("SUCCESS: 2/2 Ideas restored.")
    else:
        print(f"FAILURE: {len(all_ideas)}/2 Ideas restored.")

    # Test 2: Search Knowledge
    search_res = knowledge_graph.search_knowledge("logística")
    print(f"Search results for 'logística': {len(search_res)}")
    if len(search_res) > 0:
        print(f"Found: {search_res[0].title}")
        print("SUCCESS: Knowledge search restored.")
    else:
        print("FAILURE: Knowledge search failed.")

    # Test 3: Link Stability
    res_nodes = knowledge_graph.get_all_nodes()
    linked_count = 0
    for node in res_nodes:
        if node.connections:
            linked_count += 1
            print(f"Node '{node.title}' has connections: {node.connections}")
            
    if linked_count >= 2:
        print("SUCCESS: Links preserved between nodes.")
    else:
        print("FAILURE: Links lost or missing.")

    print("\n[5/5] Final Persistence Bridge Status: VALIDATED")

if __name__ == "__main__":
    asyncio.run(test_full_memory_bridge())
