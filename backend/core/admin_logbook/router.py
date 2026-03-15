from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from .manager import admin_manager
from .models import SuggestionStatus
from backend.core.permissions import enforce_permission, get_current_user_id

router = APIRouter()

@router.get("/logs")
async def get_admin_logs():
    enforce_permission("admin_ops_access")
    return admin_manager.list_operations()

@router.get("/suggestions/pending")
async def get_pending_suggestions():
    enforce_permission("admin_ops_access")
    return admin_manager.get_pending_suggestions()

@router.get("/checkpoints")
async def list_checkpoints():
    enforce_permission("creator_tools_access")
    return admin_manager.list_checkpoints()

@router.post("/suggestions/{suggestion_id}/review")
async def review_suggestion(suggestion_id: str, status: SuggestionStatus, notes: str = "", user_id: str = Depends(get_current_user_id)):
    enforce_permission("admin_ops_access")
    admin_manager.review_suggestion(suggestion_id, user_id, status, notes)
    return {"status": "success", "suggestion_id": suggestion_id}

@router.post("/checkpoint/create")
async def create_system_checkpoint(label: str, user_id: str = Depends(get_current_user_id)):
    enforce_permission("creator_tools_access")
    path = admin_manager.create_checkpoint(user_id, label)
    return {"status": "success", "backup_path": path}

@router.post("/rollback/{checkpoint_id}")
async def rollback_system(checkpoint_id: int, user_id: str = Depends(get_current_user_id)):
    enforce_permission("creator_tools_access")
    try:
        admin_manager.rollback_to_checkpoint(checkpoint_id, user_id)
        return {"status": "success", "message": "System restored to checkpoint"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
