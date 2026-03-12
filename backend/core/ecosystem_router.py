from fastapi import APIRouter, Depends, Request
from typing import List, Optional
from backend.core.auth import get_current_user, OmniUser
from backend.core.permissions import set_chip_context

router = APIRouter()

# --- Development ---
@router.get("/development/profile")
async def get_skill_profile(user_id: str = "default_user"):
    from backend.core.skill_engine.skill_profile_builder import skill_profile_builder
    profile = skill_profile_builder.get_profile(user_id)
    return {"status": "ok", "profile": profile.model_dump()}

@router.get("/development/opportunities")
async def get_opportunities(user_id: str = "default_user"):
    from backend.core.skill_engine.skill_profile_builder import skill_profile_builder
    from backend.core.opportunity_engine.opportunity_matcher import opportunity_matcher
    profile = skill_profile_builder.get_profile(user_id)
    matches = opportunity_matcher.find_matches(profile.top_skills)
    return {"status": "ok", "opportunities": [m.model_dump() for m in matches]}

# --- Interface ---
@router.get("/interface/windows")
async def get_active_windows():
    from backend.core.web_window_engine.web_window_controller import web_window_controller
    return {"status": "ok", "windows": [w.model_dump() for w in web_window_controller.windows.values()]}

@router.get("/interface/agents")
async def get_active_agents():
    from backend.core.multi_ai_interface.agent_manager import agent_manager
    return {"status": "ok", "agents": [a.model_dump() for a in agent_manager.get_all_agents()]}

# --- Spatial ---
@router.get("/spatial/scene")
async def get_spatial_scene():
    from backend.core.spatial_interface.spatial_scene_manager import spatial_scene_manager
    return {"status": "ok", "scene": spatial_scene_manager.active_scene.model_dump()}

# --- Economy/Factory/OS ---
@router.get("/economy/trends")
async def get_market_trends():
    from backend.core.knowledge_economy.skill_market_engine import skill_market_engine
    return {"status": "ok", "trends": [t.model_dump() for t in skill_market_engine.get_market_trends()]}

@router.get("/kernel/state")
async def get_kernel_state():
    from backend.core.knowledge_os.workspace_manager import workspace_manager
    return {"status": "ok", "state": workspace_manager.state.model_dump()}

# --- network ---
@router.get("/network/nodes")
async def get_network_nodes():
    from backend.core.distributed_network.node_registry import network_node_registry
    return network_node_registry.get_active_nodes()
