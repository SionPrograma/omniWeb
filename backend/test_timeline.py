import os
import sys
import json
import asyncio
from typing import Dict, Any

# Ensure DATA_DIR is absolute before imports
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
# Note: we are in 'backend/' or project root? The previous command used 'python backend/test_timeline.py' from project root.
# So os.getcwd() is project root.
BACKEND_DIR = os.path.join(os.getcwd(), "backend")
DATA_DIR = os.path.join(BACKEND_DIR, "data")

sys.path.append(os.getcwd())

from backend.core.config import settings
settings.DATA_DIR = DATA_DIR
print(f"DEBUG: Using DB at {settings.DATABASE_URL}")

from backend.core.ai_host.memory.memory_router import memory_router
from backend.core.ai_host.memory.project_manager import project_manager
from backend.core.ai_host.memory.idea_capture import idea_capture
from backend.core.ai_host.memory.cluster_manager import cluster_manager
from backend.core.ai_host.synthesis.synthesis_engine import synthesis_engine
from backend.core.ai_host.monitoring.project_watcher import project_watcher
from backend.core.permissions import set_chip_context

async def test_timeline():
    print("--- Testing Project Evolution Timeline ---")
    
    with set_chip_context("core"):
        # 1. Setup a dummy project if needed
        slug = "test-logistica"
        
        # Check if lineage exists
        lineage = project_manager.get_lineage(slug)
        if not lineage:
            print(f"Creating legacy data for {slug}...")
            idea = idea_capture.capture_idea("Usar drones para entrega en zonas rurales")
            cluster_manager.auto_group_ideas()
            clusters = cluster_manager.get_all_clusters()
            if clusters:
                cluster = clusters[0]
                # Generate draft
                draft = synthesis_engine.generate_project_draft(cluster)
                # Initialize
                project_manager.initialize_project(draft)
                # Get the real slug
                slug = list(project_manager.lineages.keys())[-1]
                print(f"Project initialized as: {slug}")
            else:
                print("Failed to detect clusters.")
                return

        # 2. Trigger some activity
        project_path = os.path.join(os.getcwd(), "chips", f"chip-{slug}")
        os.makedirs(project_path, exist_ok=True)
        with open(os.path.join(project_path, "test_file_timeline.py"), "w") as f:
            f.write("# Small change for timeline test\nprint('hello')")
        
        # 3. Request Timeline
        print(f"\nRequesting timeline for: {slug}")
        response = await memory_router.route_memory_task("get_project_timeline", f"ver timeline del proyecto {slug}")
        
        if response and response.status == "success":
            print("Success!")
            payload = response.payload
            timeline = payload["timeline"]
            print(f"Timeline entries: {len(timeline)}")
            for entry in timeline:
                print(f"- [{entry['type'].upper()}] {entry['title']} ({entry['description']})")
            print(f"Progress: {payload['progress']}%")
            print(f"Status: {payload['status']}")
        else:
            print(f"Failed: {response.message if response else 'No response'}")

if __name__ == "__main__":
    asyncio.run(test_timeline())
