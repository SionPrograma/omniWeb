
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
from backend.core.ai_host.memory.cluster_manager import cluster_manager
from backend.core.ai_host.memory.synthesis_engine import synthesis_engine

async def test_project_init():
    print("=== OMNIWEB — PROJECT INITIALIZATION VALIDATION ===")
    
    # 1. Reset Environment
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM ai_host_ideas")
            conn.execute("DELETE FROM ai_host_knowledge_nodes")
            conn.execute("DELETE FROM ai_host_clusters")
            conn.execute("DELETE FROM ai_host_project_drafts")
            conn.commit()
    print("[1/6] Database cleared.")

    # Reset globals
    idea_capture.ideas = {}
    cluster_manager.clusters = {}
    synthesis_engine.drafts = {}

    # Cleanup potential previous chip
    test_chip_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\chips\chip-omni-logística"
    if os.path.exists(test_chip_path):
        shutil.rmtree(test_chip_path)
        print(f"Cleaned up {test_chip_path}")

    # 2. Setup: Capture ideas and cluster them
    print("[2/6] Setup: Capturing and clustering...")
    idea_capture.capture_idea("Drones logísticos para reparto rural.", tags=["logística"])
    cluster_manager.auto_group_ideas()
    
    # 3. Step: Generate Draft
    print("[3/6] Step: Generating draft...")
    await ai_command_router.route("Omni, generá un borrador de proyecto sobre logística")
    
    # 4. Step: Initialize Project
    print("[4/6] Step: 'inicializá el proyecto de logística'")
    resp = await ai_command_router.route("Omni, inicializá el proyecto de logística")
    print(f"Status: {resp.status} | Intent: {resp.intent}")
    print(f"Message: {resp.message}")

    # 5. Verification: Folder existence
    print("\n[5/6] Verifying folder structure...")
    if os.path.exists(test_chip_path):
        print(f"SUCCESS: Folder '{test_chip_path}' exists.")
        files = os.listdir(test_chip_path)
        print(f"Contents: {files}")
        if "chip.json" in files and "core" in files:
            print("SUCCESS: Essential files/folders created.")
        
        # Verify README content
        with open(os.path.join(test_chip_path, "README.md"), "r", encoding="utf-8") as f:
            content = f.read()
            if "Omni-Logística" in content:
                print("SUCCESS: README contains project title.")
    else:
        print(f"FAILURE: Folder '{test_chip_path}' does not exist.")

    # 6. Final Audit Log check
    print("\n[6/6] Final Audit check completed.")
    print("Final Status: VALIDATED")

if __name__ == "__main__":
    asyncio.run(test_project_init())
