from fastapi import APIRouter, Depends
from typing import Dict, Any
from sqlalchemy import text

from backend.core.security.dependencies import get_current_user, get_creator_user
from backend.core.auth import OmniUser
from backend.core.database import db_manager
from .managers import scaling_manager, observability_manager
from .beta_security import beta_controller, security_auditor

router = APIRouter()


@router.get("/metrics")
async def get_metrics(current_user: OmniUser = Depends(get_creator_user)):
    return await observability_manager.get_cluster_metrics()


@router.get("/edge/nodes")
async def get_edge_nodes(current_user: OmniUser = Depends(get_creator_user)):
    return await scaling_manager.get_edge_nodes()


@router.post("/beta/invite")
async def create_invite(current_user: OmniUser = Depends(get_creator_user)):
    token = await beta_controller.create_invite_token(current_user.id)
    return {"token": token}


@router.post("/beta/feedback")
async def post_feedback(
    data: Dict[str, Any],
    current_user: OmniUser = Depends(get_current_user),
):
    await beta_controller.submit_feedback(
        current_user.id,
        data.get("feature", "general"),
        data.get("content"),
        data.get("sentiment", 0.5),
    )
    return {"status": "success"}


@router.get("/security/trail")
async def get_security_trail(current_user: OmniUser = Depends(get_creator_user)):
    async with db_manager.get_session() as session:
        res = await session.execute(
            text("SELECT * FROM security_audit_events ORDER BY timestamp DESC LIMIT 50")
        )
        rows = res.mappings().all()
        return [dict(r) for r in rows]