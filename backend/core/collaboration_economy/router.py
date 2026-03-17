from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any, Optional
from backend.core.security.dependencies import get_current_user
from backend.core.auth import OmniUser
from .managers import reputation_manager, collab_manager, ecosystem_manager
from .advanced import mentor_manager, omniverse_manager

router = APIRouter()

@router.get("/reputation")
async def get_reputation(current_user: OmniUser = Depends(get_current_user)):
    data = await reputation_manager.get_reputation(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_reputation",
        status="success",
        message="Tu perfil de reputación ha sido recuperado.",
        payload=data
    )
    unified = await orchestrator.orchestrate("get my reputation", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/projects")
async def get_projects(current_user: OmniUser = Depends(get_current_user)):
    projects = await collab_manager.get_user_projects(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="list_collab_projects",
        status="success",
        message=f"He encontrado {len(projects)} proyectos en los que colaboras.",
        payload={"projects": projects}
    )
    unified = await orchestrator.orchestrate("list my collaboration projects", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/market/listings")
async def get_listings(current_user: OmniUser = Depends(get_current_user)):
    listings = await ecosystem_manager.get_active_listings()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="list_market_listings",
        status="success",
        message="Listados activos en el mercado cargados.",
        payload={"listings": listings}
    )
    unified = await orchestrator.orchestrate("get market listings", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/mentor/state")
async def get_mentor(current_user: OmniUser = Depends(get_current_user)):
    state = await mentor_manager.get_mentor_state(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_mentor_state",
        status="success",
        message="Estado de mentoría sincronizado.",
        payload=state
    )
    unified = await orchestrator.orchestrate("get mentor status", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/omniverse/gateways")
async def get_gateways(current_user: OmniUser = Depends(get_current_user)):
    gateways = await omniverse_manager.get_user_gateways(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_omniverse_gateways",
        status="success",
        message="Accesos al Omniverso recuperados.",
        payload={"gateways": gateways}
    )
    unified = await orchestrator.orchestrate("get my omniverse gateways", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/reputation/ping")
async def ping_reputation(delta: float, reason: str, current_user: OmniUser = Depends(get_current_user)):
    await reputation_manager.update_score(current_user.id, delta, reason)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="update_reputation",
        status="success",
        message=f"Reputación actualizada ({'+' if delta >= 0 else ''}{delta}): {reason}",
        payload={"delta": delta, "reason": reason}
    )
    unified = await orchestrator.orchestrate(f"ping reputation with {delta} for {reason}", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
