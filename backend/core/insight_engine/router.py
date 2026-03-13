from fastapi import APIRouter, Depends, HTTPException
from typing import List
from backend.core.auth import get_current_user, OmniUser
from .models import ActionableInsight, InsightSummary
from .engine import insight_engine

router = APIRouter()

@router.post("/analyze", response_model=List[ActionableInsight])
async def run_analysis(current_user: OmniUser = Depends(get_current_user)):
    """
    Triggers a fresh analysis of the user's data and system state.
    """
    return await insight_engine.analyze_user(current_user.id)

@router.get("/summary", response_model=List[ActionableInsight])
async def get_insight_summary(current_user: OmniUser = Depends(get_current_user)):
    """
    Returns the latest insights for the current user.
    """
    insights = insight_engine.get_cached_insights(current_user.id)
    if not insights:
        # Auto-run first time
        insights = await insight_engine.analyze_user(current_user.id)
    return insights

@router.post("/action/{insight_id}")
async def action_insight(insight_id: str, current_user: OmniUser = Depends(get_current_user)):
    """
    Marks an insight as actioned or creates a task from it.
    """
    # In a full implementation, this could auto-create a task in the logbook
    return {"status": "success", "actioned": insight_id}
