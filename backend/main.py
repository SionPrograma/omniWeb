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
from backend.core.knowledge_domains import domain_router
from backend.core.collaboration_spaces import collaboration_router
from backend.core.user_onboarding import onboarding_router
from backend.core.logbook_network import logbook_router
from backend.core.user_context.router import router as context_router
from backend.core.ai_host.router import router as aihost_router
from backend.core.stability_loop.router import router as stability_router
from backend.core.master_logbook.router import router as master_logbook_router

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
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
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
            if parts and parts[0] not in ["system", "health", "auth", "onboarding"]:
                chip_slug = parts[0]
        token = _current_chip_ctx.set(chip_slug)
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
app.include_router(system_router, prefix=f"{settings.API_V1_STR}/system", tags=["system"])
app.include_router(edu_router, prefix=f"{settings.API_V1_STR}/education", tags=["education"])
app.include_router(ecosystem_router, prefix=f"{settings.API_V1_STR}", tags=["ecosystem"])
app.include_router(domain_router, prefix=f"{settings.API_V1_STR}/domains", tags=["domains"])
app.include_router(collaboration_router, prefix=f"{settings.API_V1_STR}/collab", tags=["collaboration"])
app.include_router(onboarding_router, prefix=f"{settings.API_V1_STR}/onboarding", tags=["onboarding"])
app.include_router(logbook_router, prefix=f"{settings.API_V1_STR}/logbook", tags=["logbook"])
app.include_router(context_router, prefix=f"{settings.API_V1_STR}/user", tags=["user"])
app.include_router(aihost_router, prefix=f"{settings.API_V1_STR}/ai-host", tags=["ai-host"])
app.include_router(stability_router, prefix=f"{settings.API_V1_STR}/system/loop", tags=["stability"])
app.include_router(master_logbook_router, prefix=f"{settings.API_V1_STR}/system/logbook", tags=["master-logbook"])

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
        # Initialize Services
        from backend.core.distributed_bus.node_health_monitor import node_health_monitor
        await node_health_monitor.start()
        from backend.core.omni_runtime.runtime_controller import runtime_controller
        await runtime_controller.initialize()
        from backend.core.distributed_network.node_discovery import node_discovery
        await node_discovery.start()
        from backend.core.idea_cloud.idea_background_processor import idea_background_processor
        await idea_background_processor.start()

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
    router_path = f"chips.chip-{module_name}.core.router"
    module_registry.register_module(
        app=app,
        module_name=module_name,
        router_import_path=router_path,
        prefix=f"{settings.API_V1_STR}/{module_name}"
    )

app.mount("/shell", StaticFiles(directory="frontend/shell"), name="shell_static")
app.mount("/dashboard-static", StaticFiles(directory="frontend/dashboard"), name="dashboard_static")
app.mount("/core", StaticFiles(directory="core"), name="core_static")

if __name__ == "__main__":
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=True)
