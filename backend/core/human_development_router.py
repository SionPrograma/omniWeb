from fastapi import APIRouter, Security, Depends, HTTPException
from typing import List, Optional, Dict, Any
from backend.core.security.dependencies import get_current_user, get_creator_user
from backend.core.auth import OmniUser
from backend.core.knowledge_os.knowledge_store import knowledge_store
from backend.core.knowledge_graph.processor import global_graph_processor
from backend.core.education_engine.learning_path import learning_path_engine
from backend.core.certification_engine.manager import certification_engine
from backend.core.opportunity_engine.processor import opportunity_engine
from backend.core.interface.accessibility import accessibility_layer

router = APIRouter()

@router.get("/knowledge/units")
async def get_knowledge_units(k_type: Optional[str] = None, current_user: OmniUser = Depends(get_current_user)):
    return await knowledge_store.get_units(k_type)

@router.get("/graph/galaxy")
async def get_graph_galaxy(current_user: OmniUser = Depends(get_current_user)):
    return await global_graph_processor.get_graph_data()

@router.get("/learning/paths")
async def get_learning_paths(current_user: OmniUser = Depends(get_current_user)):
    return await learning_path_engine.get_user_paths(current_user.id)

@router.get("/opportunities")
async def get_opportunities(current_user: OmniUser = Depends(get_current_user)):
    return await opportunity_engine.match_opportunities(current_user.id)

@router.get("/accessibility/profile")
async def get_accessibility(current_user: OmniUser = Depends(get_current_user)):
    return await accessibility_layer.get_profile(current_user.id)

@router.post("/accessibility/profile")
async def update_accessibility(data: Dict[str, Any], current_user: OmniUser = Depends(get_current_user)):
    await accessibility_layer.update_profile(current_user.id, data)
    return {"status": "success"}
