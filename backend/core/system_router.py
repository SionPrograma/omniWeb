from fastapi import APIRouter, Security, Depends, Request, HTTPException
from typing import List, Optional
import shutil
import time
import os
from backend.core.config import settings
from backend.core.module_registry import module_registry
from backend.core.database import db_manager
from backend.core.auth import get_admin_user, get_current_user, OmniUser
from backend.core.permissions import set_chip_context

router = APIRouter()

START_TIME = time.time()

@router.get("/health")
async def health_check():
    total, used, free = shutil.disk_usage(".")
    disk_ok = free > (100 * 1024 * 1024)
    db_ok = False
    migration_status = "unknown"
    try:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                db_ok = True
                row = conn.execute("SELECT COUNT(*) as cnt FROM system_migrations").fetchone()
                migration_status = f"{row['cnt']} applied"
    except Exception:
        pass

    uptime = int(time.time() - START_TIME)
    status = "ok" if (disk_ok and db_ok) else "degraded"
    
    return {
        "status": status,
        "service": "omniweb-core",
        "version": settings.VERSION,
        "uptime_seconds": uptime,
        "diagnostics": {
            "disk_free_mb": free // (1024 * 1024),
            "db_connected": db_ok,
            "migrations": migration_status
        }
    }

@router.get("/chips")
async def get_system_chips():
    chips = module_registry.get_active_modules()
    return [c for c in chips if c.get("metadata", {}).get("dashboard_visible", True)]

@router.get("/nodes")
async def get_nodes():
    from backend.core.distributed_bus.node_registry import node_registry
    return node_registry.get_active_nodes()

@router.get("/stats")
async def get_system_stats():
    active_chips = module_registry.get_active_modules()
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT COUNT(id) as total FROM system_events").fetchone()
            total_events = row["total"] if row else 0
    return {
        "status": "ok",
        "chips_active": len(active_chips),
        "events_tracked": total_events
    }

@router.get("/usage")
async def get_system_usage():
    from backend.core.usage.usage_tracker import usage_tracker
    with set_chip_context("core"):
        stats = usage_tracker.get_statistics()
    return {"status": "ok", "usage": stats}

@router.get("/runtime")
async def get_system_runtime():
    from backend.core.omni_runtime.runtime_controller import runtime_controller
    return {"status": "ok", "runtime": runtime_controller.get_runtime_summary()}

@router.get("/memory")
async def get_system_memory(current_user: OmniUser = Depends(get_current_user)):
    from backend.core.long_memory.memory_store import memory_store
    return memory_store.get_memories()

@router.get("/proposals")
async def get_system_proposals():
    from backend.core.self_improvement.proposal_engine import proposal_engine
    with set_chip_context("core"):
        proposals = proposal_engine.get_pending_proposals()
    return {"status": "ok", "proposals": proposals}

@router.get("/graph")
async def get_knowledge_graph():
    from backend.core.knowledge_graph.graph_store import GraphStore
    with set_chip_context("core"):
        store = GraphStore()
        nodes = store.get_all_nodes()
        return {"status": "ok", "nodes": [n.model_dump() for n in nodes]}

@router.get("/antimodal")
async def get_antimodal_status():
    from backend.core.antimodal.antimodal_controller import antimodal_controller
    return antimodal_controller.get_status_summary()

@router.post("/antimodal/mode")
async def set_antimodal_mode(mode: str):
    from backend.core.antimodal.antimodal_controller import antimodal_controller
    from backend.core.antimodal.antimodal_models import AntimodalMode
    try:
        new_mode = AntimodalMode(mode)
        antimodal_controller.set_mode(new_mode)
        return {"status": "success", "mode": new_mode.value}
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid antimodal mode: {mode}")

@router.post("/graph/sync")
async def sync_knowledge_graph(admin_user: dict = Security(get_admin_user)):
    from backend.core.knowledge_graph.graph_builder import GraphBuilder
    with set_chip_context("core"):
        builder = GraphBuilder()
        builder.process_all_memories()
        return {"status": "success", "message": "Graph synchronized with long-term memory."}

@router.post("/semantic/sync")
async def sync_semantic_layer(admin_user: dict = Security(get_admin_user)):
    from backend.core.semantic_layer.embedding_synchronizer import embedding_synchronizer
    with set_chip_context("core"):
        await embedding_synchronizer.sync_all()
        return {"status": "success", "message": "Semantic layer synchronized."}

@router.get("/semantic/summary")
async def get_semantic_summary():
    from backend.core.semantic_layer.vector_store import vector_store
    return vector_store.get_summary()

@router.get("/ideas")
async def get_ideas():
    from backend.core.idea_cloud.idea_store import idea_store
    return {"status": "ok", "ideas": [i.model_dump() for i in idea_store.get_recent_ideas()]}

@router.get("/ideas/clusters")
async def get_idea_clusters():
    from backend.core.idea_cloud.idea_store import idea_store
    return {"status": "ok", "clusters": [c.model_dump() for c in idea_store.get_all_clusters()]}

@router.post("/db/backup")
async def create_db_backup(admin_user: dict = Security(get_admin_user)):
    with set_chip_context("core"):
        try:
            backup_path = db_manager.backup_db()
            return {"status": "success", "backup_path": backup_path}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/db/restore")
async def restore_db_from_backup(filename: str, admin_user: dict = Security(get_admin_user)):
    data_dir = os.path.dirname(db_manager.db_path)
    source_path = os.path.join(data_dir, "backups", filename)
    with set_chip_context("core"):
        try:
            db_manager.restore_db(source_path)
            return {"status": "success", "message": f"Database restored from {filename}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/bus/receive")
async def receive_distributed_event(request: Request):
    from backend.core.distributed_bus.distributed_event_router import distributed_event_router
    body = await request.body()
    await distributed_event_router.route_incoming(body.decode())
    return {"status": "success"}
