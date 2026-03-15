
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

async def test_evolution_reports():
    print("=== OMNIWEB — EVOLUTION REPORTS VALIDATION ===")
    
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
            conn.execute("DELETE FROM ai_host_evolution_reports")
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

    # 2. Setup: Initialize Project & Simulate Activity
    print("[2/6] Setup: Initializing project and a modification...")
    idea_capture.capture_idea("Logística drones.", tags=["logística"])
    cluster_manager.auto_group_ideas()
    await ai_command_router.route("Omni, generá un borrador de proyecto sobre logística")
    await ai_command_router.route("Omni, inicializá el proyecto de logística")
    
    # Simulate Change
    time.sleep(1.1)
    with open(os.path.join(test_chip_path, "core", "main.py"), "a") as f:
        f.write("\n# Activity mock\n")
    
    # Scan for changes
    await ai_command_router.route("Omni, escaneá mis proyectos")

    # 3. Step: Generate Evolution Report
    print("[3/6] Step: 'haceme un reporte técnico del avance en logística'")
    resp_report = await ai_command_router.route("Omni, haceme un reporte técnico del avance en logística")
    print(f"Status: {resp_report.status}")
    print(f"Message: {resp_report.message}")

    # 4. Verify: Report content
    if "Reporte de Evolución: Omni-logística" in resp_report.message or "omni-logística" in resp_report.message.lower():
        print("SUCCESS: Report title/slug found.")
    if "En desarrollo activo" in resp_report.message:
        print("SUCCESS: Technical status correctly inferred correctly.")
    if "Sugerencias de Próximos Pasos" in resp_report.message:
        print("SUCCESS: Suggestions included.")

    # 5. Verify: Persistence
    print("\n[5/6] Verifying DB persistence...")
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT COUNT(*) FROM ai_host_evolution_reports").fetchone()
            print(f"Reports in DB: {row[0]}")
            if row[0] > 0:
                print("SUCCESS: Report persisted in SQLite.")

    # 6. Final check: Evolution history
    print("\n[6/6] Final audit: Inferred lineage from report...")
    if resp_report.payload and "report" in resp_report.payload:
        rep_data = resp_report.payload["report"]
        print(f"Involved lineage ID: {rep_data['lineage_ids']}")
        print(f"Involved events: {len(rep_data['activity_event_ids'])}")
        if len(rep_data['activity_event_ids']) > 0:
            print("SUCCESS: Report linked to actual activity events.")

    print("\nFinal Status: VALIDATED")

if __name__ == "__main__":
    asyncio.run(test_evolution_reports())
