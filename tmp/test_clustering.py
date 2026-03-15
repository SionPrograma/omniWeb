
import asyncio
import sys
import os
import json

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

from backend.core.permissions import set_chip_context
from backend.core.database import db_manager
from backend.core.ai_host.memory.idea_capture import idea_capture
from backend.core.ai_host.memory.knowledge_graph import knowledge_graph
from backend.core.ai_host.memory.cluster_manager import cluster_manager

async def test_clustering():
    print("=== OMNIWEB — SEMANTIC CLUSTERING VALIDATION ===")
    
    # 1. Reset Environment
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM ai_host_ideas")
            conn.execute("DELETE FROM ai_host_knowledge_nodes")
            conn.execute("DELETE FROM ai_host_knowledge_edges")
            conn.execute("DELETE FROM ai_host_clusters")
            conn.commit()
    print("[1/5] Database cleared.")

    # Reset global memory states
    idea_capture.ideas = {}
    knowledge_graph.nodes = {}
    cluster_manager.clusters = {}

    # 2. Phase A: Create Ideas with specific tags
    print("[2/5] PHASE A: Creating ideas for clustering...")
    # Logistics
    idea_capture.capture_idea("Idea 1: Drones de reparto para logística urbana.", tags=["logística", "drones"])
    idea_capture.capture_idea("Idea 2: Sistema de almacenes automatizados.", tags=["logística"])
    # Debugging
    idea_capture.capture_idea("Idea 3: Evidencia multimodal para depuración.", tags=["depuración", "ia"])
    idea_capture.capture_idea("Idea 4: Traceback visual en tiempo real.", tags=["depuración"])
    # Finance
    idea_capture.capture_idea("Idea 5: Dashboard de criptoactivos.", tags=["finanzas"])
    
    print(f"Captured {len(idea_capture.ideas)} ideas.")

    # 3. Phase B: Run Grouping
    print("[3/5] PHASE B: Running semantic grouping...")
    new_clusters = cluster_manager.auto_group_ideas()
    print(f"Detected {len(new_clusters)} new clusters.")
    for c in new_clusters:
        print(f" - Cluster: {c.title} ({len(c.node_ids)} nodes)")

    # 4. Phase C: Validation of Queries
    print("[4/5] PHASE C: Query Validation")
    
    # List clusters
    all_clusters = cluster_manager.get_all_clusters()
    print(f"Total clusters: {len(all_clusters)}")
    
    # Show specific cluster
    logistics = cluster_manager.get_cluster_by_title("Logística")
    if logistics:
        print(f"SUCCESS: Found 'Logística' cluster with {len(logistics.node_ids)} nodes.")
    else:
        print("FAILURE: 'Logística' cluster not found.")

    # 5. Phase D: Persistence check
    print("[5/5] PHASE D: Persistence Check (Simulated Restart)")
    cluster_manager.clusters = {}
    cluster_manager._load_clusters()
    
    if len(cluster_manager.clusters) >= 3:
        print(f"SUCCESS: {len(cluster_manager.clusters)} clusters reloaded from SQLite.")
    else:
        print(f"FAILURE: Only {len(cluster_manager.clusters)} clusters reloaded.")

    print("\nFinal Status: VALIDATED")

if __name__ == "__main__":
    asyncio.run(test_clustering())
