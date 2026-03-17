from fastapi import APIRouter, Security, HTTPException, Depends
from backend.core.auth import get_admin_user, OmniUser
from backend.core.permissions import set_chip_context
from backend.core.governance.manager import governance_manager
from backend.core.governance.leadership_engine import leadership_engine
from backend.core.user_memory_timeline.manager import timeline_manager
from backend.core.database import db_manager

router = APIRouter()

@router.get("/insights")
async def get_governance_insights(admin_user: OmniUser = Depends(get_admin_user)):
    """Returns all pending governance insights for the Creator."""
    insights = governance_manager.get_pending_insights()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_governance_insights",
        status="success",
        message=f"Se han identificado {len(insights)} análisis de gobernanza pendientes.",
        payload={"insights": [i.model_dump() for i in insights]}
    )
    unified = await orchestrator.orchestrate("get governance insights", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/insights/analyze")
async def run_leadership_analysis(admin_user: OmniUser = Depends(get_admin_user)):
    """Triggers the leadership detection engine to analyze all users."""
    await leadership_engine.analyze_users()
    insights = governance_manager.get_pending_insights()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="analyze_leadership",
        status="success",
        message="Análisis de liderazgo global completado. Los resultados están disponibles en el panel de gobernanza.",
        payload={"insights": [i.model_dump() for i in insights]}
    )
    unified = await orchestrator.orchestrate("analyze leadership", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/insights/{insight_id}/approve")
async def approve_insight(insight_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Approves a governance insight (e.g., promote to Admin Candidate)."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM leadership_insights WHERE id = ?", (insight_id,)).fetchone()
            if not row:
                raise HTTPException(status_code=404, detail="Insight not found.")
            conn.execute("UPDATE leadership_insights SET status = 'approved' WHERE id = ?", (insight_id,))
            # If it's a promotion insight, update user role
            if row["insight_type"] == "leadership_detection":
                conn.execute("UPDATE users SET role = 'admin_candidate' WHERE id = ?", (row["user_id"],))
            conn.commit()
            
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="approve_governance_insight",
        status="success",
        message=f"Insight {insight_id} aprobado exitosamente.",
        payload={"insight_id": insight_id, "action": "approved"}
    )
    unified = await orchestrator.orchestrate(f"approve insight {insight_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/insights/{insight_id}/reject")
async def reject_insight(insight_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Rejects a governance insight."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE leadership_insights SET status = 'rejected' WHERE id = ?", (insight_id,))
            conn.commit()
            
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="reject_governance_insight",
        status="success",
        message=f"Insight {insight_id} rechazado.",
        payload={"insight_id": insight_id, "action": "rejected"}
    )
    unified = await orchestrator.orchestrate(f"reject insight {insight_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/reputation/{user_id}")
async def get_user_reputation(user_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Returns the reputation score and graph edges for a user."""
    score = governance_manager.get_user_reputation_score(user_id)
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            edges = conn.execute(
                "SELECT * FROM reputation_graph_edges WHERE source_user_id = ? OR target_user_id = ? ORDER BY timestamp DESC LIMIT 20",
                (user_id, user_id)
            ).fetchall()
            
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_user_reputation",
        status="success",
        message=f"Puntuación de reputación para {user_id}: {score}.",
        payload={
            "user_id": user_id,
            "reputation_score": score,
            "interactions": [dict(e) for e in edges]
        }
    )
    unified = await orchestrator.orchestrate(f"get reputation for {user_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/timeline/{user_id}")
async def get_user_timeline(user_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Returns the AI memory timeline for a user."""
    milestones = timeline_manager.get_timeline(user_id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_user_timeline",
        status="success",
        message=f"Línea de tiempo de IA para el usuario {user_id} recuperada.",
        payload={"milestones": [m.model_dump() for m in milestones]}
    )
    unified = await orchestrator.orchestrate(f"get timeline for {user_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/beta/testers")
async def get_beta_testers(admin_user: OmniUser = Depends(get_admin_user)):
    """Returns all users with beta_tester or admin_candidate roles."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute(
                "SELECT id, username, role FROM users WHERE role IN ('beta_tester', 'admin_candidate')"
            ).fetchall()
            
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_beta_testers",
        status="success",
        message=f"He encontrado {len(rows)} usuarios en el programa Beta o Candidatos Admin.",
        payload={"testers": [dict(r) for r in rows]}
    )
    unified = await orchestrator.orchestrate("get beta testers", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/stats")
async def get_governance_stats(admin_user: OmniUser = Depends(get_admin_user)):
    """Returns overall governance metrics."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            insights_count = conn.execute("SELECT COUNT(*) as cnt FROM leadership_insights").fetchone()["cnt"]
            pending_insights = conn.execute("SELECT COUNT(*) as cnt FROM leadership_insights WHERE status = 'pending'").fetchone()["cnt"]
            edges_count = conn.execute("SELECT COUNT(*) as cnt FROM reputation_graph_edges").fetchone()["cnt"]
            timeline_count = conn.execute("SELECT COUNT(*) as cnt FROM user_memory_timeline").fetchone()["cnt"]
            
    stats = {
        "total_insights": insights_count,
        "pending_insights": pending_insights,
        "reputation_edges": edges_count,
        "timeline_entries": timeline_count
    }
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="get_governance_stats",
        status="success",
        message="Métricas globales de gobernanza y reputación.",
        payload=stats
    )
    unified = await orchestrator.orchestrate("get governance stats", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
