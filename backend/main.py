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
    from backend.runtime.runtime_manager import runtime_manager
    # Initialize runtime if not already done
    if not runtime_manager.environment:
         runtime_manager.initialize_runtime()
         
    return {
        "status": "ok",
        "runtime": runtime_manager.get_status()
    }

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
