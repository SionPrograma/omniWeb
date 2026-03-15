import os
import sys
import json
import asyncio
import time
import random
import shutil
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
from backend.core.ai_host.memory.knowledge_graph import knowledge_graph
from backend.core.ai_host.memory.cluster_manager import cluster_manager
from backend.core.ai_host.synthesis.synthesis_engine import synthesis_engine
# Import from new location to verify structure
try:
    from backend.core.ai_host.monitoring.project_watcher import project_watcher
except ImportError:
    from backend.core.ai_host.memory.project_watcher import project_watcher

from backend.core.permissions import set_chip_context

async def run_audit_lifecycle():
    print("=== OMNIWEB LIFECYCLE AUDIT ===")
    
    unique_id = str(int(time.time()))[-4:]
    unique_tag = f"audit_{unique_id}"
    
    with set_chip_context("core"):
        # 1. Idea Capture
        print(f"\n[STEP 1] Capturing Idea with tag: {unique_tag}...")
        idea_text = f"Sistema de Auditoria {unique_id}"
        resp = await ai_command_router.route(f"Omni, guardá esta idea: {idea_text} con el tag {unique_tag}")
        print(f"Result: {resp.status}")
        
        # 2. Grouping
        print("\n[STEP 2] Grouping Ideas...")
        cluster_manager.auto_group_ideas()
        clusters = cluster_manager.get_all_clusters()
        print(f"DEBUG: Total clusters in memory: {len(clusters)}")
        target_cluster = None
        for c in clusters:
            print(f"DEBUG: Cluster: {c.title} | Tags: {c.tags} | IDs: {c.node_ids}")
            if unique_tag in c.tags or unique_id in c.title:
                target_cluster = c
                break
        
        if not target_cluster:
            print("DEBUG: Target cluster not found by primary tags. Trying secondary search...")
            # Try to find cluster that contains the idea
            for c in clusters:
                for nid in c.node_ids:
                    node = knowledge_graph.get_node(nid)
                    if node and idea_text in node.description:
                        print(f"DEBUG: Match found in cluster: {c.title} via node content")
                        target_cluster = c
                        break
                if target_cluster: break

        if target_cluster:
            print(f"Cluster found: {target_cluster.title}")
            
            # 3. Draft Generation
            print(f"\n[STEP 3] Generating Project Draft for {target_cluster.title}...")
            resp_draft = await ai_command_router.route(f"Omni, generá un borrador de proyecto sobre {target_cluster.title}")
            print(f"Result: {resp_draft.status}")
            
            # 4. Initialization
            print("\n[STEP 4] Initializing Project...")
            resp_init = await ai_command_router.route(f"Omni, inicializá el proyecto del cluster {target_cluster.title}")
            if resp_init.status != "success" and "already exists" in resp_init.message:
                 print("Project already exists. Re-using slug.")
                 slug = target_cluster.title.lower().replace(" ", "-") # Heuristic
            elif resp_init.status == "success":
                slug = resp_init.payload["lineage"]["project_slug"]
                print(f"Slug: {slug}")
            else:
                print(f"Error: {resp_init.message}")
                return

            # Avoid crash if slug not found
            slug = slug if 'slug' in locals() else "omni-" + target_cluster.title.lower().replace(" ", "-")

            # 5. Modification
            print("\n[STEP 5] Modification & Watcher...")
            project_path = os.path.join(ROOT_DIR, "chips", f"chip-{slug}")
            os.makedirs(project_path, exist_ok=True)
            test_file = os.path.join(project_path, "audit_log.txt")
            with open(test_file, "w") as f:
                f.write(f"Audit trace {unique_id}")
            
            # Force scan
            project_watcher.last_scanned[slug] = 0
            new_evts = project_watcher.scan_all_projects()
            print(f"Detected {len(new_evts)} events in {slug}")
            
            # 6. Evolution Report
            print("\n[STEP 6] Generating Evolution Report...")
            resp_rep = await ai_command_router.route(f"Omni, haceme un reporte técnico de {slug}")
            print(f"Result: {resp_rep.status}")
            
            # 7. Timeline
            print("\n[STEP 7] Timeline Test...")
            resp_time = await ai_command_router.route(f"ver timeline del proyecto {slug}")
            print(f"Result: {resp_time.status}")
            if resp_time.status == "success":
                t = resp_time.payload["timeline"]
                print(f"Timeline size: {len(t)}")
                for event in t[-3:]:
                    print(f"- {event['type']}: {event['title']}")

    print("\n=== LIFECYCLE AUDIT COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(run_audit_lifecycle())
