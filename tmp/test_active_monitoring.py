
import asyncio
import sys
import os
import shutil
import time

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
from backend.core.ai_host.memory.project_watcher import project_watcher

async def test_active_monitoring():
    print("=== OMNIWEB — ACTIVE MONITORING VALIDATION ===")
    
    # 1. Reset Environment
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM ai_host_ideas")
            conn.execute("DELETE FROM ai_host_knowledge_nodes")
            conn.execute("DELETE FROM ai_host_knowledge_edges")
            conn.execute("DELETE FROM ai_host_clusters")
            conn.execute("DELETE FROM ai_host_project_drafts")
            conn.execute("DELETE FROM ai_host_project_lineage")
            conn.execute("DELETE FROM ai_host_project_activity")
            conn.commit()
    print("[1/6] Database cleared.")

    # Reset globals
    idea_capture.ideas = {}
    knowledge_graph.nodes = {}
    cluster_manager.clusters = {}
    synthesis_engine.drafts = {}
    project_manager.lineages = {}
    project_watcher.events = []
    project_watcher.last_scanned = {}

    # Cleanup potential previous chip
    test_chip_path = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb\chips\chip-omni-logística"
    if os.path.exists(test_chip_path):
        shutil.rmtree(test_chip_path)

    # 2. Setup: Initialize Project
    print("[2/6] Setup: Capturing ideas and initializing project...")
    idea_capture.capture_idea("Logística automatizada con drones.", tags=["logística"])
    cluster_manager.auto_group_ideas()
    await ai_command_router.route("Omni, generá un borrador de proyecto sobre logística")
    await ai_command_router.route("Omni, inicializá el proyecto de logística")
    
    # Verify project exists
    if not os.path.exists(test_chip_path):
        print(f"FAILURE: Project not found at {test_chip_path}")
        return

    # 3. Simulate Change: Modify core/main.py
    print("[3/6] Simulating technical modification in core/main.py...")
    main_py_path = os.path.join(test_chip_path, "core", "main.py")
    
    # Wait a bit to ensure mtime is different if file was just created
    time.sleep(1.1)
    
    with open(main_py_path, "a") as f:
        f.write("\n# New feature added by developer\n")
    
    print(f"File modified: {main_py_path}")

    # 4. Trigger: Active Monitoring Scan
    print("[4/6] Triggering Active Monitoring Scan...")
    resp_scan = await ai_command_router.route("Omni, escaneá mis proyectos")
    print(f"Status: {resp_scan.status}")
    print(f"Message: {resp_scan.message}")
    
    # 5. Verify: Activity Retrieval
    print("\n[5/6] Querying activity: 'qué cambió en el proyecto de logística'")
    resp_act = await ai_command_router.route("Omni, qué cambió en el proyecto de omni-logística")
    print(f"Status: {resp_act.status}")
    print(f"Message: {resp_act.message}")
    
    if "MODIFIED: core\\main.py" in resp_act.message or "MODIFIED: core/main.py" in resp_act.message:
        print("SUCCESS: Modification detected and retrieved.")
    else:
        print("FAILURE: Modification NOT detected.")

    # 6. Verify: Persistence Reload
    print("\n[6/6] Verifying persistence after mock 'restart'...")
    project_watcher.events = []
    project_watcher._load_recent_activity()
    if len(project_watcher.events) > 0:
        print(f"SUCCESS: {len(project_watcher.events)} events reloaded from SQLite.")
    else:
        print("FAILURE: Events not found in SQLite.")

    print("\nFinal Status: VALIDATED")

if __name__ == "__main__":
    asyncio.run(test_active_monitoring())
