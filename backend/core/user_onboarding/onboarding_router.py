from fastapi import APIRouter
from .onboarding_manager import onboarding_manager

router = APIRouter()

@router.post("/greeting")
async def process_greeting(data: dict):
    # 1. Get raw greeting data
    res = await onboarding_manager.process_initial_greeting(
        user_id=data.get("user_id", "new_user"),
        text=data.get("text"),
        browser_lang=data.get("browser_lang", "en"),
        invite_token=data.get("invite_token")
    )
    
    # 2. ENFORCE COGNITIVE PIPELINE
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    
    orchestrator = CognitiveOrchestrator()
    
    raw_res = AICommandResponse(
        intent="onboarding_greeting",
        status="success",
        message=res.get("message", "Welcome to OmniWeb."),
        payload=res
    )
    
    # Use orchestrator to naturalize and unify
    unified_res = await orchestrator.orchestrate(
        message=data.get("text", "initial_greeting"),
        understanding={"mode": "direct_response", "intent_group": "ONBOARDING"},
        context={"user_id": data.get("user_id", "new_user")},
        raw_response=raw_res
    )
    
    # Return formatted unified response
    return {"status": "ok", "payload": unified_res.model_dump()}
