from fastapi import APIRouter, Depends, Security
from pydantic import BaseModel
from typing import Dict, Any, Optional, List
from backend.core.auth import get_current_user, OmniUser
from backend.core.ai_host.memory.resource_lock_manager import resource_lock_manager
from .command_router import CommandRouter

ai_host_router = APIRouter()
ai_router = CommandRouter()

from ..execution.router import router as copilot_router
from ..execution.editor_router import router as editor_router
ai_host_router.include_router(copilot_router, prefix="/copilot", tags=["copilot"])
ai_host_router.include_router(copilot_router, prefix="/execution", tags=["execution"])
ai_host_router.include_router(editor_router, prefix="/editor", tags=["editor"])

class ProcessRequest(BaseModel):
    message: str
    modality: Optional[str] = "text"
    multimodal_evidence: List[Dict[str, Any]] = []
    source_surface: Optional[str] = "chat"

@ai_host_router.post("/process")
async def process_message(request: ProcessRequest, current_user: OmniUser = Depends(get_current_user)):
    """
    Main entry point for AI Host interactions.
    Processes natural language commands and returns adapted responses.
    """
    # Create context with user info and multimodal evidence
    context = {
        "user_id": current_user.id, 
        "username": current_user.username,
        "multimodal_evidence": request.multimodal_evidence,
        "source_surface": request.source_surface
    }
    cmd_res = await ai_router.route(request.message, modality=request.modality, context=context)
    
    # PHASE 103 (Chat Enrichment): Consult Governance Layer
    from ..observability.governance_chat_engine import chat_governance_engine
    gov_signals = await chat_governance_engine.analyze_interaction(request.message, context)
    
    # Adapt response using InterfaceAdapter if needed
    from ..interface_adapter import adapter
    formatted = adapter.format_response(cmd_res.message, cmd_res.payload)
    formatted["intent"] = cmd_res.intent # Add intent to response for frontend logic
    formatted["gov_enrichment"] = {
        "signals": [s.model_dump() for s in gov_signals],
        "count": len(gov_signals)
    }
    
    return formatted

@ai_host_router.get("/status")
async def get_host_status():
    """Returns the current status and mode of the AI Host."""
    return {
        "status": "active",
        "identity": "OmniWeb Host",
        "mode": "hybrid"
    }

@ai_host_router.get("/locks")
async def get_active_locks():
    """Returns all active resource locks for parallelism governance."""
    return resource_lock_manager.get_all_active_locks()

@ai_host_router.get("/execution/portfolio/drift/health")
async def get_portfolio_drift_health(
    limit: int = 20,
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 82: REAL-TIME PORTFOLIO DRIFT ANALYTICS.
    Aggregate cognitive health across all active missions.
    """
    from backend.core.ai_host.memory.mission_manager import mission_manager
    from backend.core.permissions import enforce_permission
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        health = mission_manager.get_portfolio_cognitive_health(limit=limit)
        return {"status": "success", "portfolio": health}
