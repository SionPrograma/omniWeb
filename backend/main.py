from fastapi import FastAPI, Security, Depends, Request
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import sys
import os

from backend.core.config import settings
from backend.core.module_registry import module_registry
from backend.core.database import db_manager
from backend.core.self_check import run_self_checks
from backend.core.permissions import _current_chip_ctx, set_chip_context
from starlette.middleware.base import BaseHTTPMiddleware

# --- Import New Routers ---
from backend.core.auth_router import router as auth_router
from backend.core.system_router import router as system_router
from backend.core.education_engine.router import router as edu_router
from backend.core.ecosystem_router import router as ecosystem_router
from backend.core.human_development_router import router as human_development_router
from backend.core.collaboration_economy.router import router as ecosystem_collab_router
from backend.core.scaling_observability.router import router as scaling_router
from backend.core.knowledge_domains import domain_router
from backend.core.collaboration_spaces import collaboration_router
from backend.core.user_onboarding import onboarding_router
from backend.core.logbook_network import logbook_router
from backend.core.user_context.router import router as context_router
from backend.core.ai_host.routing.router import ai_host_router as aihost_router
from backend.core.stability_loop.router import router as stability_router
from backend.core.master_logbook.router import router as master_logbook_router
from backend.core.identity.router import router as identity_router
from backend.core.security.creator_router import router as creator_gateway_router
from backend.core.user_logbook.router import router as user_logbook_router
from backend.core.user_graph.router import router as user_graph_router
from backend.core.insight_engine.router import router as insight_router
from backend.core.sync.router import router as sync_router
from backend.core.admin_logbook.router import router as admin_router
from backend.core.creator_control.router import router as creator_control_router
from backend.core.cluster.router import router as cluster_router
from backend.core.governance.router import router as governance_router
from backend.core.communication.communication_router import router as communication_router
from backend.core.integration_layer.integration_router import router as integration_router
from backend.core.qr_gateway.qr_gateway_router import router as qr_router
from backend.core.creator_fs.file_system_router import router as creator_fs_router
from backend.core.creator_copilot.router import router as creator_copilot_router

# Ensure the root of the project is in the Python path
sys.path.append(os.getcwd())

run_self_checks()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

# --- Middleware ---
if settings.BACKEND_CORS_ORIGINS:
    # Rule: Browser rejects "*" with credentials. We explicitly list common dev origins or use '*' without credentials.
    # Given Omni's shell uses Bearer tokens (headers) and not cookies, we can disable allow_credentials if using wildcard.
    origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
    allow_all = "*" in origins
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if not allow_all else ["*"],
        allow_credentials=not allow_all, # False if using wildcard to comply with browser security
        allow_methods=["*"],
        allow_headers=["*"],
    )

class ChipContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        prefix = f"{settings.API_V1_STR}/"
        chip_slug = "core"
        if path.startswith(prefix):
            parts = path[len(prefix):].split("/")
            if parts and parts[0] not in ["system", "health", "auth", "onboarding", "creator", "editor"]:
                chip_slug = parts[0]
        token = _current_chip_ctx.set({"chip_slug": chip_slug, "user_id": None})
        try:
            return await call_next(request)
        finally:
            _current_chip_ctx.reset(token)

app.add_middleware(ChipContextMiddleware)

# --- Base Routes ---
@app.get("/")
async def root():
    return FileResponse("frontend/shell/index.html")

@app.get("/dashboard")
async def dashboard():
    return FileResponse("frontend/dashboard/index.html")

# --- Include Modular Routers ---
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(identity_router, prefix=f"{settings.API_V1_STR}/auth", tags=["identity"])
app.include_router(creator_gateway_router, prefix=f"{settings.API_V1_STR}/creator", tags=["security-fortress"])
app.include_router(system_router, prefix=f"{settings.API_V1_STR}/system", tags=["system"])
app.include_router(edu_router, prefix=f"{settings.API_V1_STR}/education", tags=["education"])
app.include_router(ecosystem_router, prefix=f"{settings.API_V1_STR}/ecosystem", tags=["ecosystem"])
app.include_router(human_development_router, prefix=f"{settings.API_V1_STR}/human", tags=["human"])
app.include_router(ecosystem_collab_router, prefix=f"{settings.API_V1_STR}/ecosystem_collab", tags=["ecosystem-collab"])
app.include_router(scaling_router, prefix=f"{settings.API_V1_STR}/scaling", tags=["scaling-beta"])
app.include_router(domain_router, prefix=f"{settings.API_V1_STR}/domains", tags=["domains"])
app.include_router(collaboration_router, prefix=f"{settings.API_V1_STR}/collab", tags=["collaboration"])
app.include_router(onboarding_router, prefix=f"{settings.API_V1_STR}/onboarding", tags=["onboarding"])
app.include_router(user_logbook_router, prefix=f"{settings.API_V1_STR}/logbook", tags=["user-logbook"])
app.include_router(user_graph_router, prefix=f"{settings.API_V1_STR}/user/graph", tags=["user-graph"])
app.include_router(insight_router, prefix=f"{settings.API_V1_STR}/user/insights", tags=["insights"])
app.include_router(sync_router, prefix=f"{settings.API_V1_STR}/system/sync", tags=["sync"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/system/admin", tags=["admin"])
app.include_router(creator_control_router, prefix=f"{settings.API_V1_STR}/creator/control", tags=["creator-control"])
app.include_router(creator_fs_router, prefix=f"{settings.API_V1_STR}/creator/fs", tags=["creator-fs"])
app.include_router(creator_copilot_router, prefix=f"{settings.API_V1_STR}/creator/copilot", tags=["creator-copilot"])

# MISSION RESTORE: Explicitly bind the Core Editor Router (Used by editor.js)
from backend.core.ai_host.execution.editor_router import router as core_editor_router
app.include_router(core_editor_router, prefix=f"{settings.API_V1_STR}/editor", tags=["editor"])
app.include_router(cluster_router, prefix=f"{settings.API_V1_STR}/system/cluster", tags=["cluster"])
app.include_router(governance_router, prefix=f"{settings.API_V1_STR}/governance", tags=["governance"])
app.include_router(communication_router, prefix=f"{settings.API_V1_STR}/communication", tags=["communication"])
app.include_router(logbook_router, prefix=f"{settings.API_V1_STR}/logbook-network", tags=["logbook"])
app.include_router(context_router, prefix=f"{settings.API_V1_STR}/user", tags=["user"])
app.include_router(aihost_router, prefix=f"{settings.API_V1_STR}/ai-host", tags=["ai-host"])
app.include_router(stability_router, prefix=f"{settings.API_V1_STR}/system/loop", tags=["stability"])
app.include_router(master_logbook_router, prefix=f"{settings.API_V1_STR}/system/logbook", tags=["master-logbook"])
app.include_router(integration_router, prefix=f"{settings.API_V1_STR}/integration", tags=["integration"])
app.include_router(qr_router, prefix=f"{settings.API_V1_STR}/qr", tags=["qr-gateway"])

# --- AI Host & Other Core Logic ---
# Note: AI Host router is usually included within its own module, 
# ensuring main.py stays clean.

@app.on_event("startup")
async def startup_event():
    # Security Check
    if not settings.IS_ADMIN_TOKEN_SAFE:
        print("\n" + "!"*60)
        print("WARNING: Using default OMNIWEB_ADMIN_TOKEN.")
        print("THIS IS INSECURE FOR PRODUCTION ENVIRONMENTS.")
        print("!"*60 + "\n")

    with set_chip_context("core"):
        # Phase 28: Initializing Bootable Runtime (Orchestrates all sub-services)
        from backend.core.omni_runtime.runtime_controller import runtime_controller
        await runtime_controller.initialize()
        
        # Phase  integration: Connecting all domains
        from backend.core.integration_layer import start_integration_layer
        await start_integration_layer()

# Initialize Persistence
with set_chip_context("core"):
    db_manager.init_db()
    db_manager.run_migrations()

# --- Dynamic Chip Loading (Plugin System) ---
all_chips = module_registry.discover_all_chips()
for chip_metadata in all_chips:
    module_name = chip_metadata["slug"]
    if not chip_metadata.get("active", True):
        continue
    
    # Mount UI
    chip_folder = f"chip-{module_name}"
    ui_path = f"chips/{chip_folder}/frontend"
    if os.path.exists(ui_path):
        app.mount(f"/{module_name}", StaticFiles(directory=ui_path, html=True), name=f"{module_name}_ui")
    
    # Register API Router
    # --- Dynamic Router Isolation (Phase 0 Stabilization) ---
    possible_routers = [
        (f"chips/chip-{module_name}/core/router.py", f"chips.chip-{module_name}.core.router"),
        (f"chips/chip-{module_name}/backend/router.py", f"chips.chip-{module_name}.backend.router")
    ]
    
    found_import_path = None
    for file_path, import_path in possible_routers:
        if os.path.exists(file_path):
            found_import_path = import_path
            break
            
    if found_import_path:
        # Failsafe registration: ensures one bad chip doesn't stall startup
        try:
            module_registry.register_module(
                app=app,
                module_name=module_name,
                router_import_path=found_import_path,
                prefix=f"{settings.API_V1_STR}/{module_name}"
            )
        except Exception as e:
            # High-isolation fail: even if registration crashes (e.g. SyntaxError in chip),
            # we record its existence to satisfy front-end heartbeats.
            module_registry._register_module_state(module_name, None, chip_metadata)
            print(f"CRITICAL: Failed to register chip '{module_name}': {e}")
    elif chip_metadata.get("has_backend"):
         # Record as inactive backend to avoid false "core connection error"
         # by ensuring metadata is at least registered in the modules dict.
         module_registry._register_module_state(module_name, None, chip_metadata)
         print(f"WARNING: Chip '{module_name}' claims backend but no router.py found.")
    else:
         # Explicitly register frontend-only chips to satisfy auditor and health checks
         module_registry._register_module_state(module_name, None, chip_metadata)

app.mount("/shell", StaticFiles(directory="frontend/shell", html=True), name="shell_static")
app.mount("/dashboard-static", StaticFiles(directory="frontend/dashboard"), name="dashboard_static")
app.mount("/core", StaticFiles(directory="core"), name="core_static")

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
