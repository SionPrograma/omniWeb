from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any
from backend.core.security.dependencies import get_creator_user
from backend.core.auth import OmniUser
from backend.core.system_state.models import SystemMode
from .manager import creator_control_manager

router = APIRouter()

@router.get("/status")
async def get_creator_control_status(creator: OmniUser = Depends(get_creator_user)):
    mode = await creator_control_manager.get_system_mode()
    maint = await creator_control_manager.get_active_maintenance()
    announcement = await creator_control_manager.get_active_announcement()
    
    return {
        "mode": mode,
        "maintenance": maint,
        "announcement": announcement
    }

@router.post("/mode")
async def set_system_mode(mode: SystemMode, creator: OmniUser = Depends(get_creator_user)):
    await creator_control_manager.set_system_mode(mode, creator.id)
    return {"status": "success", "new_mode": mode}

@router.post("/maintenance/schedule")
async def schedule_maintenance(
    start_time: str = Body(...),
    duration: int = Body(...),
    message: str = Body(...),
    creator: OmniUser = Depends(get_creator_user)
):
    await creator_control_manager.schedule_maintenance(start_time, duration, message, creator.id)
    return {"status": "success"}

@router.post("/announcement")
async def publish_announcement(
    message: str = Body(...),
    type: str = Body("INFO"),
    expires_in_minutes: int = Body(1440),
    creator: OmniUser = Depends(get_creator_user)
):
    await creator_control_manager.publish_announcement(message, type, creator.id, expires_in_minutes)
    return {"status": "success"}

@router.post("/rollback")
async def force_rollback(label: str = Body(...), creator: OmniUser = Depends(get_creator_user)):
    try:
        res = await creator_control_manager.force_rollback(label, creator.id)
        return {"status": "success", "details": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/node/operation")
async def node_operation(
    node_id: str = Body(...),
    operation: str = Body(...), # 'drain', 'restart', 'disable', 'resume'
    creator: OmniUser = Depends(get_creator_user)
):
    # Scaffold for node operations
    from backend.core.security.manager import security_fortress
    security_fortress.log_creator_action(
        creator_id=creator.id,
        action_type="NODE_OPERATION",
        target=f"node:{node_id}",
        payload={"operation": operation}
    )
    
    # Simulate operation for now as per instructions
    return {"status": "success", "message": f"Operation {operation} triggered for node {node_id}"}
