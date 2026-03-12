from fastapi import FastAPI, Security, Depends, Request
from typing import List
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core.config import settings
from backend.core.module_registry import module_registry
from backend.core.database import db_manager
import uvicorn
import sys
import os
from fastapi.security import OAuth2PasswordRequestForm
from backend.core.auth import get_admin_user, get_current_user, OmniUser, oauth2_scheme

from backend.core.self_check import run_self_checks

# Ensure the root of the project is in the Python path so we can import modules
sys.path.append(os.getcwd())

run_self_checks()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# Set up CORS
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

from starlette.middleware.base import BaseHTTPMiddleware
from backend.core.permissions import _current_chip_ctx, set_chip_context

class ChipContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        prefix = f"{settings.API_V1_STR}/"
        chip_slug = "core" # Default to core for root/static/health routes
        
        if path.startswith(prefix):
            parts = path[len(prefix):].split("/")
            if parts and parts[0] not in ["system", "health"]:
                chip_slug = parts[0]
                
        token = _current_chip_ctx.set(chip_slug)
        try:
            return await call_next(request)
        finally:
            _current_chip_ctx.reset(token)

app.add_middleware(ChipContextMiddleware)

@app.get("/")
async def root():
    return FileResponse("frontend/dashboard/index.html")

import shutil
import time

START_TIME = time.time()

@app.get(f"{settings.API_V1_STR}/system/health")
async def health_check():
    """
    Enhanced diagnostics for product-grade observability.
    """
    # 1. Check Disk
    total, used, free = shutil.disk_usage(".")
    disk_ok = free > (100 * 1024 * 1024) # 100MB safety margin
    
    # 2. Check DB
    db_ok = False
    migration_status = "unknown"
    try:
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("SELECT 1").fetchone()
                db_ok = True
                # Check migrations
                row = conn.execute("SELECT COUNT(*) as cnt FROM system_migrations").fetchone()
                migration_status = f"{row['cnt']} applied"
    except Exception as e:
        logger.error(f"Health check DB failure: {e}")

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

@app.get(f"{settings.API_V1_STR}/system/chips")
async def get_system_chips():
    """Returns the list of all registered chips with their metadata."""
    chips = module_registry.get_active_modules()
    filtered_chips = []
    for chip in chips:
        # Control sistémico: Oculta a nivel API los chips que tienen dashboard_visible = False
        if chip.get("metadata", {}).get("dashboard_visible", True):
            filtered_chips.append(chip)
    return filtered_chips

@app.on_event("startup")
async def startup_event():
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        # Initialize Node Monitoring
        from backend.core.distributed_bus.node_health_monitor import node_health_monitor
        await node_health_monitor.start()

        # Initialize New Runtime Foundation
        from backend.core.omni_runtime.runtime_controller import runtime_controller
        await runtime_controller.initialize()

        # Initialize Distributed Network discovery
        from backend.core.distributed_network.node_discovery import node_discovery
        await node_discovery.start()
        
        # Register heartbeat listener on the bus
        from backend.core.event_bus import event_bus
        event_bus.subscribe("network_node_heartbeat", node_discovery.handle_remote_heartbeat)

        # Initialize Idea Cloud background processing (Phase Y)
        from backend.core.idea_cloud.idea_background_processor import idea_background_processor
        await idea_background_processor.start()

@app.get(f"{settings.API_V1_STR}/system/nodes")
async def get_nodes():
    """Returns list of active nodes in the distributed environment."""
    from backend.core.distributed_bus.node_registry import node_registry
    return node_registry.get_active_nodes()

@app.get(f"{settings.API_V1_STR}/system/stats")
async def get_system_stats():
    """Returns basic operational metrics from the OmniWeb environment."""
    from backend.core.permissions import set_chip_context
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

@app.get(f"{settings.API_V1_STR}/system/usage")
async def get_system_usage():
    """Returns detailed usage analytics for the Self-Improvement Engine."""
    from backend.core.usage.usage_tracker import usage_tracker
    from backend.core.permissions import set_chip_context
    
    with set_chip_context("core"):
        stats = usage_tracker.get_statistics()
        
    return {
        "status": "ok",
        "usage": stats
    }

@app.get(f"{settings.API_V1_STR}/system/runtime")
async def get_system_runtime():
    """Returns the current runtime environment and orchestration mode."""
    from backend.core.omni_runtime.runtime_controller import runtime_controller
    return {
        "status": "ok",
        "runtime": runtime_controller.get_runtime_summary()
    }

@app.get(f"{settings.API_V1_STR}/system/memory")
async def get_system_memory(current_user: OmniUser = Depends(get_current_user)):
    """Returns long term memories for the dashboard."""
    from backend.core.long_memory.memory_store import memory_store
    return memory_store.get_memories()

@app.get(f"{settings.API_V1_STR}/system/proposals")
async def get_system_proposals():
    """Returns pending system improvement proposals."""
    from backend.core.self_improvement.proposal_engine import proposal_engine
    from backend.core.permissions import set_chip_context
    
    with set_chip_context("core"):
        proposals = proposal_engine.get_pending_proposals()
        
    return {
        "status": "ok",
        "proposals": proposals
    }

@app.get(f"{settings.API_V1_STR}/user/context")
async def get_user_context():
    """Returns detected user behavioral patterns and habits."""
    from backend.core.user_context.context_model import context_model
    from backend.core.permissions import set_chip_context
    
    with set_chip_context("core"):
        patterns = context_model.get_patterns()
        
    return {
        "status": "ok",
        "patterns": patterns
    }

@app.get(f"{settings.API_V1_STR}/system/graph")
async def get_knowledge_graph():
    """Returns the current state of the knowledge graph."""
    from backend.core.knowledge_graph.graph_store import GraphStore
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        store = GraphStore()
        nodes = store.get_all_nodes()
        return {"status": "ok", "nodes": [n.model_dump() for n in nodes]}

@app.get(f"{settings.API_V1_STR}/system/antimodal")
async def get_antimodal_status():
    """Returns the current antimodal state and mode."""
    from backend.core.antimodal.antimodal_controller import antimodal_controller
    return antimodal_controller.get_status_summary()

@app.post(f"{settings.API_V1_STR}/system/antimodal/mode")
async def set_antimodal_mode(mode: str):
    """Updates the current antimodal mode."""
    from backend.core.antimodal.antimodal_controller import antimodal_controller
    from backend.core.antimodal.antimodal_models import AntimodalMode
    try:
        new_mode = AntimodalMode(mode)
        antimodal_controller.set_mode(new_mode)
        return {"status": "success", "mode": new_mode.value}
    except ValueError:
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail=f"Invalid antimodal mode: {mode}")

@app.post(f"{settings.API_V1_STR}/system/graph/sync")
async def sync_knowledge_graph(admin_user: dict = Security(get_admin_user)):
    """Triggers a manual synchronization of the knowledge graph from memory."""
    from backend.core.knowledge_graph.graph_builder import GraphBuilder
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        builder = GraphBuilder()
        builder.process_all_memories()
        return {"status": "success", "message": "Graph synchronized with long-term memory."}

@app.post(f"{settings.API_V1_STR}/system/semantic/sync")
async def sync_semantic_layer(admin_user: dict = Security(get_admin_user)):
    """Triggers a full rebuild of the semantic index."""
    from backend.core.semantic_layer.embedding_synchronizer import embedding_synchronizer
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        await embedding_synchronizer.sync_all()
        return {"status": "success", "message": "Semantic layer synchronized."}

@app.get(f"{settings.API_V1_STR}/system/semantic/summary")
async def get_semantic_summary():
    """Returns a summary of the semantic layer for dashboard visualization."""
    from backend.core.semantic_layer.vector_store import vector_store
    return vector_store.get_summary()

@app.get(f"{settings.API_V1_STR}/system/loop/status")
async def get_loop_status(task_id: str):
    """Returns the current state of a stability loop task."""
    from backend.core.stability_loop.loop_controller import loop_controller
    status = loop_controller.get_task_status(task_id)
    if not status:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")
    return status

# --- Idea Cloud Endpoints (Phase Y) ---

@app.get(f"{settings.API_V1_STR}/system/ideas")
async def get_ideas():
    """Returns recent ideas from the cloud."""
    from backend.core.idea_cloud.idea_store import idea_store
    return {"status": "ok", "ideas": [i.model_dump() for i in idea_store.get_recent_ideas()]}

@app.get(f"{settings.API_V1_STR}/system/ideas/clusters")
async def get_idea_clusters():
    """Returns emerging concept clusters."""
    from backend.core.idea_cloud.idea_store import idea_store
    return {"status": "ok", "clusters": [c.model_dump() for c in idea_store.get_all_clusters()]}

# --- Education Engine Endpoints (Phase Z) ---

@app.get(f"{settings.API_V1_STR}/education/path")
async def get_learning_path(topic: str):
    """Generates or retrieves a learning path for a topic."""
    from backend.core.education_engine.learning_path_generator import learning_path_generator
    path = learning_path_generator.generate_path(topic)
    return {"status": "ok", "path": path.model_dump()}

@app.get(f"{settings.API_V1_STR}/education/map")
async def get_concept_map(topic: str):
    """Generates a hierarchical concept map."""
    from backend.core.education_engine.concept_map_builder import concept_map_builder
    cmap = concept_map_builder.build_map(topic)
    return {"status": "ok", "concept_map": cmap.model_dump() if cmap else None}

@app.get(f"{settings.API_V1_STR}/education/profile")
async def get_learning_profile():
    """Returns the user skill and mastery profile."""
    from backend.core.education_engine.skill_tracker import skill_tracker
    profile = skill_tracker.get_user_profile()
    return {"status": "ok", "profile": [s.model_dump() for s in profile]}

@app.post(f"{settings.API_V1_STR}/education/evaluate")
async def evaluate_knowledge(topic: str, answer: str):
    """Evaluates user understanding and updates skills."""
    from backend.core.education_engine.knowledge_evaluator import knowledge_evaluator
    result = await knowledge_evaluator.evaluate_mastery(topic, answer)
    return {"status": "ok", "result": result}

@app.get(f"{settings.API_V1_STR}/education/certs")
async def get_certifications(current_user: OmniUser = Depends(get_current_user)):
    """Returns earned certifications for the current user."""
    from backend.core.education_engine.certification_engine import certification_engine
    certs = certification_engine.get_user_certifications(str(current_user.id))
    return {"status": "ok", "certifications": [c.model_dump() for c in certs]}

# --- Human Development Network (Phase AA) ---

@app.get(f"{settings.API_V1_STR}/development/profile")
async def get_skill_profile(user_id: str = "default_user"):
    """Returns the unified skill and cognitive profile."""
    from backend.core.skill_engine.skill_profile_builder import skill_profile_builder
    profile = skill_profile_builder.get_profile(user_id)
    return {"status": "ok", "profile": profile.model_dump()}

@app.get(f"{settings.API_V1_STR}/development/opportunities")
async def get_opportunities(user_id: str = "default_user"):
    """Analyzes market demand and matches with user skills."""
    from backend.core.skill_engine.skill_profile_builder import skill_profile_builder
    from backend.core.opportunity_engine.opportunity_matcher import opportunity_matcher
    profile = skill_profile_builder.get_profile(user_id)
    matches = opportunity_matcher.find_matches(profile.top_skills)
    return {"status": "ok", "opportunities": [m.model_dump() for m in matches]}

@app.post(f"{settings.API_V1_STR}/development/award-cert")
async def award_certificate(title: str, skills: list[str], level: str = "Foundation"):
    """Manually awards a certification (Admin/Verified source)."""
    from backend.core.certification_engine.certification_generator import certification_generator
    cert = certification_generator.award_certification("default_user", title, skills, level)
    return {"status": "ok", "certification": cert.model_dump()}

# --- Multi-AI Interface (Phase AB) ---

@app.get(f"{settings.API_V1_STR}/interface/windows")
async def get_active_windows():
    """Returns all active floating windows."""
    from backend.core.web_window_engine.web_window_controller import web_window_controller
    return {"status": "ok", "windows": [w.model_dump() for w in web_window_controller.windows.values()]}

@app.get(f"{settings.API_V1_STR}/interface/agents")
async def get_active_agents():
    """Returns all invited AI participants."""
    from backend.core.multi_ai_interface.agent_manager import agent_manager
    return {"status": "ok", "agents": [a.model_dump() for a in agent_manager.get_all_agents()]}

@app.get(f"{settings.API_V1_STR}/interface/config")
async def get_interface_config():
    """Returns global theme and transparency settings."""
    from backend.core.web_window_engine.web_window_controller import web_window_controller
    return {"status": "ok", "config": web_window_controller.config.model_dump()}

# --- Spatial Interface (Phase AC) ---

@app.get(f"{settings.API_V1_STR}/spatial/scene")
async def get_spatial_scene():
    """Returns the current 3D holographic scene state."""
    from backend.core.spatial_interface.spatial_scene_manager import spatial_scene_manager
    return {"status": "ok", "scene": spatial_scene_manager.active_scene.model_dump()}

@app.post(f"{settings.API_V1_STR}/spatial/transform")
async def update_spatial_transform(obj_id: str, x: float = None, y: float = None, z: float = None):
    """Updates position of a holographic object."""
    from backend.core.spatial_interface.spatial_scene_manager import spatial_scene_manager
    from backend.core.spatial_interface.spatial_models import Vector3
    pos = Vector3(x=x, y=y, z=z) if x is not None else None
    spatial_scene_manager.update_object(obj_id, position=pos)
    return {"status": "ok"}

@app.post(f"{settings.API_V1_STR}/spatial/gesture")
async def process_spatial_gesture(gesture: str, obj_id: str = None):
    """Processes a simulated hand gesture."""
    from backend.core.spatial_interface.gesture_processor import gesture_processor
    res = gesture_processor.process_gesture(gesture, obj_id)
    return res

# --- V2.0 Universal Knowledge OS & Economy ---

@app.get(f"{settings.API_V1_STR}/economy/trends")
async def get_market_trends():
    """Returns global skill demand and economic trends."""
    from backend.core.knowledge_economy.skill_market_engine import skill_market_engine
    return {"status": "ok", "trends": [t.model_dump() for t in skill_market_engine.get_market_trends()]}

@app.post(f"{settings.API_V1_STR}/factory/evolve")
async def trigger_chip_evolution(topics: List[str]):
    """Analyzes topics to automatically design new chips."""
    from backend.core.self_evolving_factory.idea_cluster_analyzer import idea_cluster_analyzer
    from backend.core.self_evolving_factory.automatic_chip_designer import automatic_chip_designer
    clusters = idea_cluster_analyzer.analyze_emergence(topics)
    blueprints = [automatic_chip_designer.design_from_cluster(c) for c in clusters]
    return {"status": "ok", "evolved_blueprints": [b.model_dump() for b in blueprints]}

@app.get(f"{settings.API_V1_STR}/system/kernel/state")
async def get_kernel_state():
    """Returns the unified Knowledge OS workspace state."""
    from backend.core.knowledge_os.workspace_manager import workspace_manager
    return {"status": "ok", "state": workspace_manager.state.model_dump()}

# --- Phase AH - Language Bridge ---

@app.post(f"{settings.API_V1_STR}/bridge/config")
async def set_bridge_config(config: dict):
    """Updates the user configuration for the translation bridge."""
    from backend.core.language_bridge.conversation_bridge import conversation_bridge, BridgeUserConfig
    user_id = config.get("user_id", "default_user")
    new_config = BridgeUserConfig(**config)
    await conversation_bridge.set_user_config(user_id, new_config)
    return {"status": "ok"}

@app.post(f"{settings.API_V1_STR}/bridge/utterance")
async def process_bridge_utterance(data: dict):
    """Processes a spoken segment for translation and delivery."""
    from backend.core.language_bridge.conversation_bridge import conversation_bridge, LanguageCode
    speaker_data = data.get("speaker", {})
    from backend.core.language_bridge.language_bridge_models import Speaker
    speaker = Speaker(**speaker_data)
    
    res = await conversation_bridge.process_utterance(
        speaker, 
        data.get("text", ""), 
        data.get("recipient_id", "default_user")
    )
    return {"status": "ok", "payload": res}

# --- Phase AI - Global Communication ---

@app.get(f"{settings.API_V1_STR}/comm/active")
async def get_active_sessions():
    """Lists all currently active global translation sessions."""
    from backend.core.global_communication.session_manager import session_manager
    sessions = session_manager.get_active_sessions()
    return {"status": "ok", "sessions": [s.model_dump() for s in sessions]}

@app.post(f"{settings.API_V1_STR}/comm/sessions")
async def create_comm_session(data: dict):
    """Initializes a new global communication session."""
    from backend.core.global_communication.session_manager import session_manager, Participant
    from backend.core.language_bridge.language_bridge_models import LanguageCode
    
    creator_data = data.get("creator", {})
    creator = Participant(
        user_id=creator_data.get("user_id", "default"),
        name=creator_data.get("name", "User"),
        native_language=LanguageCode(creator_data.get("lang", "es")),
        listening_language=LanguageCode(creator_data.get("listen", "es"))
    )
    session = session_manager.create_session(data.get("title", "Call"), creator)
    return {"status": "ok", "session": session.model_dump()}

# --- Distributed Network Endpoints (Phase V) ---

@app.get(f"{settings.API_V1_STR}/network/nodes")
async def get_network_nodes():
    """Returns the specialized knowledge node registry."""
    from backend.core.distributed_network.node_registry import network_node_registry
    return network_node_registry.get_active_nodes()

@app.get(f"{settings.API_V1_STR}/network/knowledge/bundle")
async def get_knowledge_bundle():
    """Serves local knowledge nodes to requesting peers."""
    from backend.core.distributed_network.knowledge_sync import knowledge_sync_manager
    from backend.core.distributed_network.security import network_security
    # For now, we allow bundle sharing without explicit node auth for easier discovery
    # but we'd normally guard this.
    return knowledge_sync_manager.get_local_bundle()

@app.get(f"{settings.API_V1_STR}/network/knowledge/search")
async def search_remote_knowledge(query: str, threshold: float = 0.3):
    """Answers semantic queries from remote nodes."""
    from backend.core.semantic_layer.search_engine import semantic_query_engine
    return await semantic_query_engine.search(query, threshold=threshold)

@app.post(f"{settings.API_V1_STR}/network/sync")
async def trigger_network_sync(node_id: str):
    """Manually triggers a pull-sync from a specific remote node."""
    from backend.core.distributed_network.knowledge_sync import knowledge_sync_manager
    return await knowledge_sync_manager.request_sync(node_id)

@app.post(f"{settings.API_V1_STR}/system/proposals/execute")
async def execute_proposal(proposal_id: int):
    """Executes a system improvement proposal through the stability loop."""
    from backend.core.self_improvement.proposal_engine import proposal_engine
    return await proposal_engine.execute_proposal(proposal_id)

@app.post(f"{settings.API_V1_STR}/system/runtime/profile")
async def switch_runtime_profile(profile: str):
    """Switches the active runtime profile using the Stability Loop."""
    from backend.core.omni_runtime.runtime_controller import runtime_controller
    return await runtime_controller.switch_profile(profile)

@app.post(f"{settings.API_V1_STR}/system/bus/receive")
async def receive_distributed_event(request: Request):
    """Receives an event from a remote OmniWeb node."""
    from backend.core.distributed_bus.distributed_event_router import distributed_event_router
    body = await request.body()
    await distributed_event_router.route_incoming(body.decode())
    return {"status": "success"}

@app.post(f"{settings.API_V1_STR}/system/db/backup")
async def create_db_backup(admin_user: dict = Security(get_admin_user)):
    """Triggers an online backup of the SQLite database."""
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        try:
            backup_path = db_manager.backup_db()
            return {"status": "success", "backup_path": backup_path}
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))

@app.post(f"{settings.API_V1_STR}/system/db/restore")
async def restore_db_from_backup(filename: str, admin_user: dict = Security(get_admin_user)):
    """Triggers a restore from a specific backup file in the backups folder."""
    from backend.core.permissions import set_chip_context
    data_dir = os.path.dirname(db_manager.db_path)
    source_path = os.path.join(data_dir, "backups", filename)
    
    with set_chip_context("core"):
        try:
            db_manager.restore_db(source_path)
            return {"status": "success", "message": f"Database restored from {filename}"}
        except Exception as e:
            from fastapi import HTTPException
            raise HTTPException(status_code=500, detail=str(e))

@app.post(f"{settings.API_V1_STR}/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user and returns a persistent session token.
    """
    from backend.core.auth import get_user_by_username, verify_password, create_session
    from fastapi import HTTPException
    
    # 2. Verify and potentially upgrade hash
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute(
                "SELECT id, hashed_password FROM users WHERE username = ?",
                (form_data.username,)
            ).fetchone()
            
            if not row or not verify_password(form_data.password, row["hashed_password"]):
                raise HTTPException(status_code=400, detail="Incorrect username or password")
            
            user_id = row["id"]
            current_hash = row["hashed_password"]

            # Lazy Hash Upgrade: If it's not bcrypt, update it now
            from backend.core.auth import get_password_hash
            if not (current_hash.startswith("$2b$") or current_hash.startswith("$2a$")):
                new_hash = get_password_hash(form_data.password)
                conn.execute(
                    "UPDATE users SET hashed_password = ? WHERE id = ?",
                    (new_hash, user_id)
                )
                conn.commit()
                print(f"DEBUG: Upgraded password hash for user {form_data.username}")

    # 3. Create persistent session
    token = create_session(user_id)
    
    return {"access_token": token, "token_type": "bearer"}

@app.get(f"{settings.API_V1_STR}/auth/me")
async def get_my_profile(current_user: OmniUser = Security(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user

@app.post(f"{settings.API_V1_STR}/auth/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Inactivates the current session token."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
    return {"status": "success", "message": "Logged out successfully"}

# Mount Core static resources
app.mount("/core", StaticFiles(directory="core"), name="core_static")

# Initialize Persistence Layer
with set_chip_context("core"):
    db_manager.init_db()
    db_manager.run_migrations()

# Discover and Register Modules (Phase 4: Plugin Installer approach)
all_chips = module_registry.discover_all_chips()

for chip_metadata in all_chips:
    module_name = chip_metadata["slug"]
    
    # 1. Mount UI (if active)
    if not chip_metadata.get("active", True):
        # We still register it in memory as 'inactive' but don't mount routes
        continue

    chip_folder = f"chip-{module_name}"
    ui_path = f"chips/{chip_folder}/frontend"
    
    if os.path.exists(ui_path):
        app.mount(f"/{module_name}", StaticFiles(directory=ui_path, html=True), name=f"{module_name}_ui")
        print(f"Mounted UI for {module_name} at /{module_name}")

    # 2. Register API Router
    router_path = f"chips.chip-{module_name}.core.router"
    module_registry.register_module(
        app=app,
        module_name=module_name,
        router_import_path=router_path,
        prefix=f"{settings.API_V1_STR}/{module_name}"
    )



if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
