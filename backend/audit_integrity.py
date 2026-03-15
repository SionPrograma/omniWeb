import os
import sys
import json
import asyncio
import time
import sqlite3

# Ensure DATA_DIR is absolute
ROOT_DIR = os.getcwd()
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
DATA_DIR = os.path.join(BACKEND_DIR, "data")
sys.path.append(ROOT_DIR)

from backend.core.config import settings
settings.DATA_DIR = DATA_DIR

from backend.core.database import db_manager
from backend.core.ai_host.memory.project_manager import project_manager
from backend.core.ai_host.memory.idea_capture import idea_capture
from backend.core.ai_host.memory.cluster_manager import cluster_manager
from backend.core.ai_host.synthesis.synthesis_engine import synthesis_engine
from backend.core.ai_host.monitoring.project_watcher import project_watcher
from backend.core.permissions import set_chip_context

async def audit_integrity():
    print("=== OMNIWEB ARCHITECTURAL AUDIT ===")
    
    with set_chip_context("core"):
        # 1. DB Schema & Foreign Keys
        print("\n[AUDIT] Database Schema & Foreign Keys...")
        with db_manager.get_connection() as conn:
            # Check PRAGMA foreign_keys
            fk_status = conn.execute("PRAGMA foreign_keys").fetchone()[0]
            print(f"PRAGMA foreign_keys: {'ON' if fk_status else 'OFF'}")
            
            # Check for orphans in ProjectLineage
            lineages = conn.execute("SELECT * FROM ai_host_project_lineage").fetchall()
            print(f"Lineage entries: {len(lineages)}")
            for row in lineages:
                # source_draft_id
                did = row["source_draft_id"]
                if did:
                    exists = conn.execute("SELECT id FROM ai_host_project_drafts WHERE id = ?", (did,)).fetchone()
                    if not exists:
                        print(f"!!! ORPHAN: Lineage {row['project_slug']} refers to missing draft {did}")
                
                # source_cluster_id
                cid = row["source_cluster_id"]
                if cid:
                    exists = conn.execute("SELECT id FROM ai_host_clusters WHERE id = ?", (cid,)).fetchone()
                    if not exists:
                        print(f"!!! ORPHAN: Lineage {row['project_slug']} refers to missing cluster {cid}")

        # 2. Memory Synchronization (In-Memory vs DB)
        print("\n[AUDIT] Memory Synchronization...")
        print(f"IdeaCapture ideas in memory: {len(idea_capture.ideas)}")
        print(f"ClusterManager clusters in memory: {len(cluster_manager.clusters)}")
        print(f"ProjectManager lineages in memory: {len(project_manager.lineages)}")
        print(f"SynthesisEngine drafts in memory: {len(synthesis_engine.drafts)}")
        
        # 3. Watcher Efficiency
        print("\n[AUDIT] Watcher Configuration...")
        print(f"Watcher events in memory: {len(project_watcher.events)}")
        print(f"Last scanned projects: {list(project_watcher.last_scanned.keys())}")

    print("\n=== AUDIT COMPLETE ===")

if __name__ == "__main__":
    asyncio.run(audit_integrity())
