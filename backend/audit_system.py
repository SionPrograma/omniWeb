import os
import sys
import json
import asyncio
import time
from typing import Dict, Any

# Ensure DATA_DIR is absolute before imports
ROOT_DIR = os.getcwd()
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
DATA_DIR = os.path.join(BACKEND_DIR, "data")
sys.path.append(ROOT_DIR)

from backend.core.config import settings
settings.DATA_DIR = DATA_DIR

from backend.core.ai_host import ai_command_router
from backend.core.ai_host.memory.memory_router import memory_router
from backend.core.ai_host.memory.project_manager import project_manager
from backend.core.ai_host.memory.idea_capture import idea_capture
from backend.core.ai_host.memory.cluster_manager import cluster_manager
from backend.core.ai_host.synthesis.synthesis_engine import synthesis_engine
from backend.core.ai_host.monitoring.project_watcher import project_watcher
from backend.core.permissions import set_chip_context

async def run_audit_test():
    print("=== OMNIWEB SYSTEM AUDIT TEST ===")
    
    with set_chip_context("core"):
        # 1. Capture Idea
        print("\n[TEST 1] Create Idea...")
        msg_idea = "Omni, guardá esta idea: un sistema de riego inteligente con IA"
        resp_idea = await ai_command_router.route(msg_idea)
        print(f"Result: {resp_idea.status} | {resp_idea.message}")
        
        # 2. Cluster Grouping
        print("\n[TEST 2] Cluster Grouping...")
        # Force clustering
        clusters = cluster_manager.auto_group_ideas()
        riego_cluster = cluster_manager.get_cluster_by_title("Riego")
        if riego_cluster:
            print(f"Cluster found: {riego_cluster.title} (Nodes: {len(riego_cluster.node_ids)})")
        else:
            print("Cluster not found by title, listing all...")
            for c in cluster_manager.get_all_clusters():
                print(f"- {c.title}")
            riego_cluster = cluster_manager.get_all_clusters()[0] if cluster_manager.get_all_clusters() else None

        # 3. Project Initialization
        print("\n[TEST 3] Project Initialization...")
        if riego_cluster:
            msg_init = f"Omni, inicializá el proyecto del cluster {riego_cluster.title}"
            resp_init = await ai_command_router.route(msg_init)
            print(f"Result: {resp_init.status}")
            if resp_init.status == "success":
                slug = resp_init.payload["lineage"]["project_slug"]
                print(f"Slug: {slug}")
            else:
                print(f"Error: {resp_init.message}")
                # Fallback if already initialized
                slug = "riego-inteligente" if "riego" in riego_cluster.title.lower() else list(project_manager.lineages.keys())[-1]
        else:
            print("Skipping initialization, no cluster.")
            return

        # 4. File Modification
        print("\n[TEST 4] File Modification...")
        project_path = os.path.join(ROOT_DIR, "chips", f"chip-{slug}")
        os.makedirs(project_path, exist_ok=True)
        test_file = os.path.join(project_path, "logic.py")
        with open(test_file, "w") as f:
            f.write("# Modified for audit test\ndef water(): pass")
        
        # Scan projects
        new_events = project_watcher.scan_all_projects()
        print(f"Detected {len(new_events)} new events in {slug}")

        # 5. Evolution Report
        print("\n[TEST 5] Evolution Report Generation...")
        msg_report = f"Omni, haceme un reporte técnico de {slug}"
        resp_report = await ai_command_router.route(msg_report)
        print(f"Result: {resp_report.status}")
        if resp_report.status == "success":
            print("Report generated successfully.")

        # 6. Timeline Request
        print("\n[TEST 6] Timeline Visualization (Direct Call)...")
        msg_timeline = f"ver timeline del proyecto {slug}"
        resp_timeline = await ai_command_router.route(msg_timeline)
        print(f"Result: {resp_timeline.status}")
        if resp_timeline.status == "success":
            timeline = resp_timeline.payload["timeline"]
            print(f"Events found: {len(timeline)}")
            for e in timeline[-3:]: # Show last 3
                print(f"- {e['type']}: {e['title']}")

    print("\n=== AUDIT TEST COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_audit_test())
