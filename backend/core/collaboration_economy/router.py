from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from backend.core.security.dependencies import get_current_user
from backend.core.auth import OmniUser
from .managers import reputation_manager, collab_manager, ecosystem_manager
from .advanced import mentor_manager, omniverse_manager

router = APIRouter()

@router.get("/reputation")
async def get_reputation(current_user: OmniUser = Depends(get_current_user)):
    return await reputation_manager.get_reputation(current_user.id)

@router.get("/projects")
async def get_projects(current_user: OmniUser = Depends(get_current_user)):
    return await collab_manager.get_user_projects(current_user.id)

@router.get("/market/listings")
async def get_listings(current_user: OmniUser = Depends(get_current_user)):
    return await ecosystem_manager.get_active_listings()

@router.get("/mentor/state")
async def get_mentor(current_user: OmniUser = Depends(get_current_user)):
    return await mentor_manager.get_mentor_state(current_user.id)

@router.get("/omniverse/gateways")
async def get_gateways(current_user: OmniUser = Depends(get_current_user)):
    return await omniverse_manager.get_user_gateways(current_user.id)

@router.post("/reputation/ping")
async def ping_reputation(delta: float, reason: str, current_user: OmniUser = Depends(get_current_user)):
    await reputation_manager.update_score(current_user.id, delta, reason)
    return {"status": "success"}
