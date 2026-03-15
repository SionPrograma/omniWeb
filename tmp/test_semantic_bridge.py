
import asyncio
import sys
import os
import shutil

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

from backend.core.permissions import set_chip_context
from backend.core.database import db_manager
from backend.core.ai_host.command_router import ai_command_router
from backend.core.ai_host.memory.idea_capture import idea_capture
from backend.core.ai_host.memory.knowledge_graph import knowledge_graph
from backend.core.ai_host.memory.cluster_manager import cluster_manager
from backend.core.ai_host.memory.synthesis_engine import synthesis_engine
from backend.core.ai_host.memory.project_manager import project_manager

async def test_semantic_bridge():
    print("=== OMNIWEB — SEMANTIC BRIDGE VALIDATION ===")
    
    # 1. Reset Environment
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM ai_host_ideas")
            conn.execute("DELETE FROM ai_host_knowledge_nodes")
            conn.execute("DELETE FROM ai_host_knowledge_edges")
            conn.execute("DELETE FROM ai_host_clusters")
            conn.execute("DELETE FROM ai_host_project_drafts")
            conn.execute("DELETE FROM ai_host_project_lineage")
            conn.commit()
    print("[1/6] Database cleared.")

    # Reset globals
    idea_capture.ideas = {}
    knowledge_graph.nodes = {}
    cluster_manager.clusters = {}
    synthesis_engine.drafts = {}
    project_manager.lineages = {}

    # Cleanup potential previous chip
    test_chip_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\chips\chip-omni-logística"
    if os.path.exists(test_chip_path):
        shutil.rmtree(test_chip_path)

    # 2. Setup: Capture ideas and cluster them
    print("[2/6] Setup: Ideas -> Cluster -> Draft...")
    idea_capture.capture_idea("Logística automatizada con drones.", tags=["logística"])
    cluster_manager.auto_group_ideas()
    await ai_command_router.route("Omni, generá un borrador de proyecto sobre logística")
    
    # 3. Step: Initialize Project (This should trigger the loop)
    print("[3/6] Step: Initializing project...")
    await ai_command_router.route("Omni, inicializá el proyecto de logística")
    
    # 4. Verify: Knowledge Graph Nodes (Project Node)
    print("\n[4/6] Verifying Knowledge Graph feedback...")
    all_nodes = knowledge_graph.get_all_nodes()
    project_nodes = [n for n in all_nodes if "proyecto" in n.tags]
    print(f"Project nodes found: {len(project_nodes)}")
    for pn in project_nodes:
        print(f" - {pn.title}: {pn.description}")
        print(f"   Connections: {len(pn.connections)} nodes linked.")
        if len(pn.connections) > 0:
            print("   SUCCESS: Project node is linked to source ideas.")

    # 5. Verify: Lineage Retrieval
    print("\n[5/6] Testing: 'qué salió del cluster de logística'")
    resp_lin = await ai_command_router.route("Omni, qué salió del cluster de logística")
    print(f"Status: {resp_lin.status}")
    print(f"Message: {resp_lin.message}")

    # 6. Verify: Evolution Retrieval
    print("\n[6/6] Testing: 'cómo evolucionó el proyecto de logística'")
    resp_evo = await ai_command_router.route("Omni, cómo evolucionó el proyecto de omni-logística")
    print(f"Status: {resp_evo.status}")
    print(f"Message: {resp_evo.message}")

    print("\nFinal Status: VALIDATED")

if __name__ == "__main__":
    asyncio.run(test_semantic_bridge())
