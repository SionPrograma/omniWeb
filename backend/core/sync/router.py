from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List
from backend.core.auth import OmniUser, get_current_user
from .manager import sync_manager
from .models import SyncPackage

router = APIRouter()

@router.post("/register")
async def register_device(
    device_id: str, 
    device_name: str, 
    metadata: Dict[str, Any] = {},
    user: OmniUser = Depends(get_current_user)
):
    """Registers a device for the current user."""
    success = sync_manager.register_device(user.id, device_id, device_name, metadata)
    return {"status": "success" if success else "failed"}

@router.get("/devices")
async def list_devices(user: OmniUser = Depends(get_current_user)):
    """Lists registered sync devices."""
    return sync_manager.get_devices(user.id)

@router.get("/package")
async def get_sync_package(user: OmniUser = Depends(get_current_user)):
    """Prepares an incremental sync package for the user."""
    # Simulation: In a real scenario, this would track the specific device's last sync
    package = sync_manager.prepare_package(user.id)
    return package

@router.post("/ingest")
async def ingest_sync_package(
    package: SyncPackage,
    user: OmniUser = Depends(get_current_user)
):
    """Processes an incoming sync package."""
    if package.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized sync target.")
    
    results = sync_manager.ingest_package(package)
    return {"status": "success", "results": results}

@router.get("/status")
async def get_sync_status(user: OmniUser = Depends(get_current_user)):
    """Returns general sync health and recent logs."""
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            logs = conn.execute(
                "SELECT * FROM sync_audit_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
                (user.id,)
            ).fetchall()
            devices = conn.execute("SELECT COUNT(*) as count FROM sync_devices WHERE user_id = ?", (user.id,)).fetchone()
            
            return {
                "devices_count": devices["count"],
                "recent_logs": [dict(r) for r in logs],
                "health": "stable" if devices["count"] > 0 else "unconfigured"
            }
