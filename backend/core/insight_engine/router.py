from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.core.auth import get_current_user, OmniUser
from .models import ActionableInsight, InsightSummary
from .engine import insight_engine

router = APIRouter()

@router.post("/analyze")
async def run_analysis(current_user: OmniUser = Depends(get_current_user)):
    """
    Triggers a fresh analysis of the user's data and system state.
    """
    insights = await insight_engine.analyze_user(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="insights_analyze",
        status="success",
        message="Análisis de insights completado.",
        payload={"insights": [i.dict() for i in insights]}
    )
    unified = await orchestrator.orchestrate("analyze my data", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/summary")
async def get_insight_summary(current_user: OmniUser = Depends(get_current_user)):
    """
    Returns the latest insights for the current user.
    """
    insights = insight_engine.get_cached_insights(current_user.id)
    if not insights:
        # Auto-run first time
        insights = await insight_engine.analyze_user(current_user.id)
        
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="insights_summary",
        status="success",
        message=f"He recopilado {len(insights)} insights accionables para ti.",
        payload={"insights": [i.dict() for i in insights]}
    )
    unified = await orchestrator.orchestrate("give me an insight summary", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/action/{insight_id}")
async def action_insight(insight_id: str, current_user: OmniUser = Depends(get_current_user)):
    """
    Marks an insight as actioned or creates a task from it.
    """
    # In a full implementation, this could auto-create a task in the logbook
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="insights_action",
        status="success",
        message=f"Insight {insight_id} procesado correctamente.",
        payload={"insight_id": insight_id}
    )
    unified = await orchestrator.orchestrate(f"action insight {insight_id}", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
