from fastapi import FastAPI, Security, Depends
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
from backend.core.auth import get_admin_user

# Ensure the root of the project is in the Python path so we can import modules
sys.path.append(os.getcwd())

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

@app.get(f"{settings.API_V1_STR}/system/health")
async def health_check():
    return {"status": "ok", "service": "omniweb-core"}

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

@app.post(f"{settings.API_V1_STR}/auth/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """Basic auth flow for obtaining admin token."""
    from fastapi import HTTPException
    # For OmniWeb local OS, user/password can be bypassed if client knows the ADMIN_TOKEN via env
    # or simple check (e.g. login with any username, password=ADMIN_TOKEN)
    if form_data.password != settings.ADMIN_TOKEN:
        raise HTTPException(status_code=400, detail="Incorrect username or password")
    
    return {"access_token": settings.ADMIN_TOKEN, "token_type": "bearer"}

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
