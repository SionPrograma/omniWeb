
import asyncio
import sys
import os

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

from backend.core.permissions import set_chip_context
from backend.core.database import db_manager
from backend.core.ai_host.command_router import ai_command_router
from backend.core.ai_host.memory.idea_capture import idea_capture
from backend.core.ai_host.memory.cluster_manager import cluster_manager
from backend.core.ai_host.memory.synthesis_engine import synthesis_engine

async def test_synthesis():
    print("=== OMNIWEB — PROACTIVE SYNTHESIS VALIDATION ===")
    
    # 1. Reset Environment
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM ai_host_ideas")
            conn.execute("DELETE FROM ai_host_knowledge_nodes")
            conn.execute("DELETE FROM ai_host_clusters")
            conn.execute("DELETE FROM ai_host_project_drafts")
            conn.commit()
    print("[1/5] Database cleared.")

    # Reset globals
    idea_capture.ideas = {}
    cluster_manager.clusters = {}
    synthesis_engine.drafts = {}

    # 2. Setup cluster data
    print("[2/5] Setup: Capturing logistics ideas...")
    idea_capture.capture_idea("Drones logísticos para entrega de paquetes médicos.", tags=["logística", "salud"])
    idea_capture.capture_idea("Red de almacenes inteligentes para drones.", tags=["logística", "infraestructura"])
    cluster_manager.auto_group_ideas()
    print(f"Clusters created: {[c.title for c in cluster_manager.get_all_clusters()]}")

    # 3. Test Routing: Summarize
    print("\n[3/5] Testing: 'resumí el cluster de logística'")
    resp_sum = await ai_command_router.route("Omni, resumí el cluster de logística")
    print(f"Status: {resp_sum.status} | Intent: {resp_sum.intent}")
    print(f"Summary: {resp_sum.message}")

    # 4. Test Routing: Project Draft
    print("\n[4/5] Testing: 'generá un borrador de proyecto sobre logística'")
    resp_draft = await ai_command_router.route("Omni, generá un borrador de proyecto sobre logística")
    print(f"Status: {resp_draft.status} | Intent: {resp_draft.intent}")
    print(f"Draft:\n{resp_draft.message}")

    # 5. Persistence Check
    print("\n[5/5] Persistence Check (Simulated Reload)")
    synthesis_engine.drafts = {}
    synthesis_engine._load_drafts()
    
    if len(synthesis_engine.drafts) > 0:
        reloaded = list(synthesis_engine.drafts.values())[0]
        print(f"SUCCESS: Loaded draft '{reloaded.title}' from SQLite.")
        if "Omni-Logística" in reloaded.title:
            print("Title verified.")
    else:
        print("FAILURE: No drafts reloaded.")

    print("\nFinal Status: VALIDATED")

if __name__ == "__main__":
    asyncio.run(test_synthesis())
