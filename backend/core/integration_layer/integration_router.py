from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from .integration_registry import integration_registry
from backend.core.auth import get_current_user, OmniUser

router = APIRouter(prefix="/system/integration", tags=["Integration Layer"])

@router.get("/status")
async def get_integration_status(current_user: OmniUser = Depends(get_current_user)):
    """Returns the status of all active domain bridges."""
    bridges = integration_registry.list_bridges()
    data = {
        "status": "active",
        "active_bridges": bridges,
        "total_connections": len(bridges)
    }
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="integration_status",
        status="success",
        message=f"Capa de integración activa. {len(bridges)} puentes de dominio identificados.",
        payload=data
    )
    unified = await orchestrator.orchestrate("get integration status", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/health")
async def get_integration_health(current_user: OmniUser = Depends(get_current_user)):
    """Health check for the integration layer."""
    data = {"status": "healthy", "layer": "Integration Core"}
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="integration_health",
        status="success",
        message="Salud de la capa de integración verificada.",
        payload=data
    )
    unified = await orchestrator.orchestrate("check integration health", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
