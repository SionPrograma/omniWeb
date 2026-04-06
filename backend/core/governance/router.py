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
@router.get("/forensic/cockpit")
async def get_forensic_cockpit(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE FORENSIC DECISION DASHBOARD.
    Consolidates all historical action traces and evaluates global decision health.
    """
    from backend.core.ai_host.observability.governance_trace_engine import trace_engine
    with set_chip_context("core"):
        dashboard_data = trace_engine.get_forensic_dashboard()
        
    return {"status": "success", "payload": dashboard_data}

@router.get("/forensic/heatmap")
async def get_friction_heatmap(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE FRICTION HEATMAP.
    Returns the spatial friction nodes per domain.
    """
    from backend.core.ai_host.observability.governance_heatmap_engine import heatmap_engine
    with set_chip_context("core"):
        heatmap = heatmap_engine.get_friction_heatmap()
        
    return {"status": "success", "payload": [node.model_dump() for node in heatmap]}

@router.post("/forensic/relief/generate")
async def generate_relief_proposals(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE RECOVERY MISSION GENERATOR.
    Forces a scan of hotspots to generate structural relief proposals.
    """
    from backend.core.ai_host.observability.governance_relief_engine import relief_engine
    with set_chip_context("core"):
        proposals = relief_engine.generate_proposals()
    return {"status": "success", "payload": [p.model_dump() for p in proposals]}

@router.get("/forensic/relief/proposals")
async def get_active_relief_proposals(domain: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE RECOVERY MISSION GENERATOR.
    Returns all PENDING relief proposals for the Creator to review.
    """
    from backend.core.ai_host.observability.governance_relief_engine import relief_engine
    with set_chip_context("core"):
        proposals = relief_engine.get_active_proposals(domain=domain)
    return {"status": "success", "payload": [p.model_dump() for p in proposals]}

@router.post("/forensic/relief/proposals/{proposal_id}/decision")
async def decide_relief_proposal(proposal_id: str, decision: str, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE RECOVERY MISSION GENERATOR.
    Registers Creator's decision (ACCEPT, REJECT, POSTPONE) over a proposal.
    """
    from backend.core.ai_host.observability.governance_relief_engine import relief_engine
    from backend.core.governance.ledger_engine import governance_ledger_engine
    with set_chip_context("core"):
        result = relief_engine.process_decision(proposal_id, decision)
        
        # Record in Ledger (PHASE 109)
        with db_manager.get_connection() as conn:
            p = conn.execute("SELECT * FROM governance_relief_proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
            if p:
                governance_ledger_engine.record_decision(
                    decision_type="RELIEF_MISSION_DECISION",
                    target_ref_type="DOMAIN",
                    target_id=p["target_domain"],
                    actor="CREATOR",
                    action_taken=decision,
                    rationale=f"Intervención de alivio en dominio {p['target_domain']}. Objetivo: {p['suggested_objective']}",
                    evidence_refs={"proposal_id": proposal_id, "risk_level": p["suggested_risk"]},
                    severity_context=p["suggested_risk"]
                )
    return result

@router.post("/forensic/relief/evaluate")
async def evaluate_relief_effectiveness(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE DRIFT RADAR ENHANCEMENT.
    Trigger evaluation of all active relief missions.
    """
    from backend.core.ai_host.observability.governance_resistance_engine import resistance_engine
    with set_chip_context("core"):
        evals = resistance_engine.evaluate_all_active_reliefs()
    return {"status": "success", "payload": [ev.model_dump() for ev in evals]}

@router.get("/forensic/relief/evaluation/{proposal_id}")
async def get_mission_evaluation(proposal_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE DRIFT RADAR ENHANCEMENT.
    Returns the latest stabilization outcome for a specific mission.
    """
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM governance_relief_proposals WHERE proposal_id = ?", (proposal_id,)).fetchone()
            if not row: return {"status": "error", "message": "Evaluation not found"}
            return {"status": "success", "payload": dict(row)}

@router.get("/forensic/audit/needs")
async def scan_root_cause_audit_needs(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: FORENSIC ROOT CAUSE AUDIT TRIGGER.
    Scans for resistant hotspots and suggests deep audits.
    """
    from backend.core.ai_host.observability.governance_audit_trigger_engine import audit_trigger_engine
    with set_chip_context("core"):
        proposals = audit_trigger_engine.scan_for_audit_needs()
    return {"status": "success", "payload": [p.model_dump() for p in proposals]}

@router.get("/forensic/audit/proposals")
async def get_root_cause_audit_proposals(domain: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: FORENSIC ROOT CAUSE AUDIT TRIGGER.
    Returns pending or accepted root cause investigations.
    """
    from backend.core.ai_host.observability.governance_audit_trigger_engine import audit_trigger_engine
    with set_chip_context("core"):
        proposals = audit_trigger_engine.get_proposals(domain=domain)
    return {"status": "success", "payload": [p.model_dump() for p in proposals]}

@router.post("/forensic/audit/proposals/{audit_id}/decision")
async def decide_root_cause_audit(audit_id: str, decision: str, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: FORENSIC ROOT CAUSE AUDIT TRIGGER.
    Process Creator decision over a structural audit proposal.
    """
    from backend.core.ai_host.observability.governance_audit_trigger_engine import audit_trigger_engine
    with set_chip_context("core"):
        result = audit_trigger_engine.process_decision(audit_id, decision)
    return result

@router.get("/forensic/autopsy")
async def get_branch_autopsies(branch_id: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: FORENSIC BRANCH AUTOPSY.
    Returns generated post-mortem reports for experiment branches.
    """
    from backend.core.ai_host.observability.governance_autopsy_engine import autopsy_engine
    with set_chip_context("core"):
        results = autopsy_engine.get_autopsies(branch_id=branch_id)
    return {"status": "success", "payload": [a.model_dump() for a in results]}

@router.post("/forensic/autopsy/{branch_id}")
async def trigger_branch_autopsy(branch_id: str, outcome: str, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: FORENSIC BRANCH AUTOPSY.
    Manually triggers a forensic autopsy for a branch.
    """
    from backend.core.ai_host.observability.governance_autopsy_engine import autopsy_engine
    with set_chip_context("core"):
        result = autopsy_engine.generate_autopsy(branch_id, outcome)
    if not result: return {"status": "error", "message": "Failed to generate autopsy."}
    return {"status": "success", "payload": result.model_dump()}

@router.get("/learning/surface")
async def get_learning_surface(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE LEARNING SURFACE.
    Returns consolidated structural learnings.
    """
    from backend.core.ai_host.observability.governance_learning_engine import learning_engine
    with set_chip_context("core"):
        results = learning_engine.get_learnings()
    return {"status": "success", "payload": [l.model_dump() for l in results]}

@router.post("/learning/surface/scan")
async def refresh_learning_surface(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE LEARNING SURFACE.
    Triggers re-aggregation of structural learning items.
    """
    from backend.core.ai_host.observability.governance_learning_engine import learning_engine
    with set_chip_context("core"):
        results = learning_engine.refresh_learning_surface()
    return {"status": "success", "payload": [l.model_dump() for l in results]}

@router.get("/mobile/summary")
async def get_mobile_governance_summary(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: MOBILE UX GOVERNANCE PASS.
    Returns counts of urgent governance items for mobile badges.
    """
    from backend.core.ai_host.observability.governance_heatmap_engine import heatmap_engine
    from backend.core.ai_host.observability.governance_relief_engine import relief_engine
    from backend.core.ai_host.observability.governance_trace_engine import trace_engine
    from backend.core.ai_host.observability.governance_predictive_engine import predictive_engine
    
    with set_chip_context("core"):
        # 1. Hotspots
        heatmap = heatmap_engine.get_friction_heatmap()
        critical_hotspots = [n for n in heatmap if n.severity_band in ["CRITICAL", "HOT"]]
        
        # 2. Proposals
        proposals = relief_engine.get_active_proposals()
        
        # 3. Traces to evaluate
        traces = trace_engine.evaluate_active_traces()
        pending_outcomes = [t for t in traces if t.outcome_status == "PENDING_OUTCOME"]

        # 4. Predictive
        predictive = predictive_engine.get_active_advisories()
        predictive_urgent = [p for p in predictive if p.predictive_state in ["HIGH_DRIFT_PROBABILITY", "PREVENTIVE_ACTION_RECOMMENDED"]]
        
    return {
        "status": "success",
        "payload": {
            "critical_hotspots": len(critical_hotspots),
            "pending_proposals": len(proposals),
            "pending_outcomes": len(pending_outcomes),
            "predictive_signals": len(predictive_urgent),
            "max_severity": max([n.friction_score for n in heatmap]) if heatmap else 0
        }
    }

@router.get("/predictive/active")
async def get_active_predictive_advisories(domain: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE PREDICTIVE DRIFT ADVISOR.
    Returns current preventive advisories.
    """
    from backend.core.ai_host.observability.governance_predictive_engine import predictive_engine
    return {"status": "success", "payload": [a.model_dump() for a in predictive_engine.get_active_advisories(domain=domain)]}

@router.post("/predictive/advisories/{advisory_id}/decision")
async def decide_predictive_advisory(advisory_id: str, decision: str, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE PREDICTIVE DRIFT ADVISOR.
    Registers Creator's decision over a prediction.
    """
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE governance_predictive_advisories SET is_active = 0 WHERE advisory_id = ?", (advisory_id,))
            adv = conn.execute("SELECT * FROM governance_predictive_advisories WHERE advisory_id = ?", (advisory_id,)).fetchone()
            if not adv: return {"status": "error", "message": "Advisory not found."}
            from backend.core.ai_host.observability.governance_trace_engine import trace_engine
            trace = trace_engine.register_trace(target_id=advisory_id, action=f"PREDICTIVE_{decision}", target_type="PREDICTIVE_ADVISORY", domain=adv["target_domain"])
            conn.commit()
    return {"status": "success", "message": f"Decisión {decision} registrada.", "trace_id": trace.trace_id}

@router.post("/copilot/enrich")
async def enrich_mission_draft(
    payload: Dict[str, Any],
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 102: MISSION CO-PILOT ENRICHMENT.
    Enriches mission proposals with governance insights (drift, debt, patterns) 
    during initial design or review.
    """
    from backend.core.ai_host.observability.governance_copilot_engine import governance_copilot
    
    objective = payload.get("objective", "")
    surface = payload.get("surface", [])
    
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        signals = await governance_copilot.analyze_draft(objective, surface)
        
        return {
            "status": "success", 
            "count": len(signals),
            "signals": [s.model_dump() for s in signals]
        }

@router.post("/trace/interaction")
async def trace_interaction(
    payload: Dict[str, Any],
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 103: GOVERNANCE INTERACTION TRACING.
    Logs how the creator reacted to a conversational governance signal.
    """
    signal_id = payload.get("signal_id")
    action = payload.get("action")
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE governance_chat_signals 
                SET status = ? 
                WHERE signal_id = ?
            """, ("APPLIED" if action == "apply" else "IGNORED", signal_id))
            conn.commit()
            
    return {"status": "success", "signal_id": signal_id, "action_logged": action}

@router.get("/synergy/scan")
async def scan_branch_synergies(current_user: OmniUser = Depends(get_current_user)):
    """
    PHASE 104: CROSS-BRANCH SYNERGY ANALYSIS.
    Triggers a manual scan of active branches to detect collisions and opportunities.
    """
    from ..ai_host.observability.cross_branch_engine import branch_synergy_engine
    with set_chip_context("governance", current_user.id):
        relations = branch_synergy_engine.scan_active_branches()
        return {"status": "success", "count": len(relations), "relations": [r.model_dump() for r in relations]}

@router.get("/synergy/relations")
async def get_branch_relations(current_user: OmniUser = Depends(get_current_user)):
    """Retrieves all active cross-branch relations."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM branch_synergy_relations WHERE status = 'ACTIVE'").fetchall()
            return {"status": "success", "relations": [dict(r) for r in rows]}

@router.get("/consolidation/proposals")
async def get_consolidation_proposals(current_user: OmniUser = Depends(get_current_user)):
    """PHASE 105: REDUNDANT BRANCH CONSOLIDATION. Retrieves active proposals."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM branch_consolidations WHERE state = 'PROPOSED'").fetchall()
            return {"status": "success", "proposals": [dict(r) for r in rows]}

@router.post("/consolidation/act")
async def act_on_consolidation(
    payload: Dict[str, Any],
    current_user: OmniUser = Depends(get_current_user)
):
    """Logs the creator's decision on a consolidation proposal."""
    cons_id = payload.get("consolidation_id")
    action = payload.get("action") # ACCEPT, REJECT, POSTPONE, ESCALATE
    
    with set_chip_context("core"):
        from backend.core.governance.ledger_engine import governance_ledger_engine
        with db_manager.get_connection() as conn:
            new_state = "ACCEPTED" if action == "ACCEPT" else "REJECTED" if action == "REJECT" else "POSTPONED"
            creator_action = "ESCALATED" if action == "ESCALATE" else None
            
            # Fetch data for ledger before updating
            cons = conn.execute("SELECT * FROM branch_consolidations WHERE consolidation_id = ?", (cons_id,)).fetchone()
            
            conn.execute("""
                UPDATE branch_consolidations 
                SET state = ?, creator_action = ?, updated_at = CURRENT_TIMESTAMP
                WHERE consolidation_id = ?
            """, (new_state, creator_action, cons_id))
            
            # Record in Ledger (PHASE 109)
            if cons:
                governance_ledger_engine.record_decision(
                    decision_type="BRANCH_CONSOLIDATION",
                    target_ref_type="BRANCH",
                    target_id=cons["primary_branch_id"],
                    actor="CREATOR",
                    action_taken=action,
                    rationale=f"Consolidación de {cons['secondary_branch_id']} en {cons['primary_branch_id']}. Tipo: {cons['consolidation_type']}. {cons['rationale']}",
                    evidence_refs={"consolidation_id": cons_id, "secondary_branch": cons['secondary_branch_id']},
                    severity_context="MODERATE"
                )
            
            conn.commit()
            
    return {"status": "success", "consolidation_id": cons_id, "action": action}

@router.get("/investment/audit")
async def get_investment_audits(current_user: OmniUser = Depends(get_current_user)):
    """PHASE 106: TACTICAL INVESTMENT AUDIT. Retrieves ROI audits for branches."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM branch_investment_audits ORDER BY value_score DESC").fetchall()
            return {"status": "success", "audits": [dict(r) for r in rows]}

@router.get("/investment/audit/{branch_id}")
async def get_branch_investment_audit(branch_id: str, current_user: OmniUser = Depends(get_current_user)):
    """Retrieves the investment audit for a specific branch."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM branch_investment_audits WHERE branch_id = ?", (branch_id,)).fetchone()
            return {"status": "success", "audit": dict(row) if row else None}

@router.get("/investment/scan")
async def run_investment_scan(current_user: OmniUser = Depends(get_current_user)):
    """Triggers the Tactical Investment Audit Engine."""
    from backend.core.ai_host.observability.investment_audit_engine import investment_audit_engine
    audits = investment_audit_engine.audit_branches()
    return {"status": "success", "audits_performed": len(audits)}

@router.post("/investment/predict/{branch_id}")
async def trigger_predictive_roi_analysis(branch_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Triggers ROI projection for a branch based on history."""
    from backend.core.ai_host.observability.predictive_roi_engine import predictive_roi_engine
    with set_chip_context("core"):
        projection = predictive_roi_engine.analyze_branch_prospect(branch_id)
        if not projection:
            return {"status": "success", "payload": None}
    return {"status": "success", "payload": projection.model_dump()}

@router.get("/investment/predict/all")
async def get_active_roi_projections(admin_user: OmniUser = Depends(get_admin_user)):
    """Returns all active ROI projections."""
    from backend.core.ai_host.observability.predictive_roi_engine import predictive_roi_engine
    with set_chip_context("core"):
        projections = predictive_roi_engine.get_projections()
    return {"status": "success", "payload": [p.model_dump() for p in projections]}

@router.get("/investment/predict/{branch_id}")
async def get_branch_roi_projection(branch_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Returns ROI projection for a specific branch."""
    from backend.core.ai_host.observability.predictive_roi_engine import predictive_roi_engine
    with set_chip_context("core"):
        projections = predictive_roi_engine.get_projections(branch_id=branch_id)
        if not projections:
            return {"status": "success", "payload": None}
    return {"status": "success", "payload": projections[0].model_dump()}

@router.post("/investment/suggest/{branch_id}")
async def trigger_alternative_path_analysis(branch_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Triggers analysis for better tactical paths."""
    from backend.core.ai_host.observability.alternative_path_engine import alternative_path_engine
    with set_chip_context("core"):
        suggestions = alternative_path_engine.generate_suggestions(branch_id)
    return {"status": "success", "count": len(suggestions), "payload": [s.model_dump() for s in suggestions]}

@router.get("/investment/suggest/all")
async def get_all_alternative_paths(admin_user: OmniUser = Depends(get_admin_user)):
    """Returns all active tactical suggestions."""
    from backend.core.ai_host.observability.alternative_path_engine import alternative_path_engine
    with set_chip_context("core"):
        suggestions = alternative_path_engine.get_suggestions()
    return {"status": "success", "payload": [s.model_dump() for s in suggestions]}

@router.post("/investment/suggest/action")
async def register_suggestion_action(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """Updates status for a tactical suggestion."""
    path_id = payload.get("path_id")
    action = payload.get("action") # ACCEPT, IGNORE, POSTPONE
    from backend.core.governance.ledger_engine import governance_ledger_engine
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            new_status = "ACCEPTED" if action == "ACCEPT" else "IGNORED" if action == "IGNORE" else "POSTPONED"
            conn.execute("UPDATE branch_alternative_paths SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE path_id = ?", (new_status, path_id))
            
            # Record in Ledger (PHASE 109)
            sug = conn.execute("SELECT * FROM branch_alternative_paths WHERE path_id = ?", (path_id,)).fetchone()
            if sug:
                governance_ledger_engine.record_decision(
                    decision_type="ALTERNATIVE_PATH_ACTION",
                    target_ref_type="BRANCH",
                    target_id=sug["branch_id"],
                    actor="CREATOR",
                    action_taken=new_status,
                    rationale=f"Sugerencia táctica de tipo {sug['path_type']}: {sug['proposed_strategy']}",
                    evidence_refs={"path_id": path_id, "path_type": sug["path_type"]},
                    severity_context="MODERATE"
                )
            conn.commit()
    return {"status": "success", "path_id": path_id, "new_status": new_status}

@router.post("/predictive/scan")
async def run_predictive_scan(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE PREDICTIVE DRIFT ADVISOR.
    Forces a predictive drift analysis.
    """
    from backend.core.ai_host.observability.governance_predictive_engine import predictive_engine
    advisories = predictive_engine.scan_drift_signals()
    return {"status": "success", "payload": [a.model_dump() for a in advisories]}

@router.post("/predictive/action")
async def register_predictive_action(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """Registers Creator's decision on a predictive warning."""
    advisory_id = payload.get("advisory_id")
    action = payload.get("action") # ATTEND, IGNORE
    from backend.core.governance.ledger_engine import governance_ledger_engine
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            # Note: Assuming table 'governance_predictive_advisories' exists from PHASE 107
            adv = conn.execute("SELECT * FROM governance_predictive_advisories WHERE advisory_id = ?", (advisory_id,)).fetchone()
            if adv:
                governance_ledger_engine.record_decision(
                    decision_type="PREDICTIVE_SIGNAL_DECISION",
                    target_ref_type="DOMAIN",
                    target_id=adv["affected_domain"],
                    actor="CREATOR",
                    action_taken=action,
                    rationale=f"Alerta predictiva ({adv['drift_type']}): {adv['rationale']}. Acción decidida: {action}",
                    evidence_refs={"advisory_id": advisory_id, "prob_degradation": adv["prob_degradation"]},
                    severity_context=adv["severity"]
                )
            
            # Record action in local table if state management exists
            conn.execute("UPDATE governance_predictive_advisories SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE advisory_id = ?", (action, advisory_id))
            conn.commit()
    return {"status": "success", "advisory_id": advisory_id, "action": action}

@router.get("/ledger/all")
async def get_governance_ledger(decision_type: str = None, target_id: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE DECISION LEDGER.
    Returns the strategic book of high-level decisions.
    """
    from backend.core.governance.ledger_engine import governance_ledger_engine
    with set_chip_context("core"):
        ledger = governance_ledger_engine.get_ledger(filter_type=decision_type, target_id=target_id)
    return {"status": "success", "payload": [dict(entry) for entry in ledger]}

@router.post("/ledger/outcome")
async def update_ledger_outcome(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """Manual or system update of decision outcomes."""
    target_id = payload.get("target_id")
    outcome = payload.get("outcome") # EFFECTIVE, DEGRADED, FAILED
    from backend.core.governance.ledger_engine import governance_ledger_engine
    with set_chip_context("core"):
        governance_ledger_engine.update_outcome(target_id, outcome)
    return {"status": "success", "target_id": target_id, "new_outcome": outcome}

@router.get("/consensus/all")
async def get_consensus_advisories(current_user: OmniUser = Depends(get_current_user)):
    """PHASE 110: GOVERNANCE CONSENSUS ADVISOR. Returns behavioral pattern advisories."""
    from backend.core.governance.consensus_engine import consensus_engine
    advisories = consensus_engine.get_active_advisories()
    return {"status": "success", "payload": [a.model_dump() for a in advisories]}

@router.post("/consensus/scan")
async def trigger_consensus_scan(admin_user: OmniUser = Depends(get_admin_user)):
    """Forces a scan of the decision ledger to detect biases."""
    from backend.core.governance.consensus_engine import consensus_engine
    advisories = consensus_engine.scan_bias_patterns()
    return {"status": "success", "count": len(advisories), "payload": [a.model_dump() for a in advisories]}

@router.post("/consensus/action")
async def act_on_consensus_advisory(payload: dict, current_user: OmniUser = Depends(get_current_user)):
    """Registers Creator's response to a consensus advisory (ATTEND, IGNORE)."""
    advisory_id = payload.get("advisory_id")
    action = payload.get("action")
    from backend.core.governance.consensus_engine import consensus_engine
    consensus_engine.act_on_advisory(advisory_id, action)
    return {"status": "success", "advisory_id": advisory_id, "action": action}

@router.get("/recalibration/proposals")
async def get_recalibration_proposals(status: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 111: GOVERNANCE CONSENSUS FEEDBACK LOOP. Returns recalibration proposals."""
    from backend.core.governance.feedback_engine import feedback_engine
    proposals = feedback_engine.get_proposals(status=status)
    return {"status": "success", "payload": [p.model_dump() for p in proposals]}

@router.post("/recalibration/generate")
async def trigger_recalibration_draft(admin_user: OmniUser = Depends(get_admin_user)):
    """Triggers translation of active consensus advisories into recalibration proposals."""
    from backend.core.governance.feedback_engine import feedback_engine
    proposals = feedback_engine.generate_proposals()
    return {"status": "success", "count": len(proposals), "payload": [p.model_dump() for p in proposals]}

@router.post("/recalibration/execute")
async def execute_recalibration(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """Applies a proposed recalibration after Creator approval."""
    rid = payload.get("recalibration_id")
    from backend.core.governance.feedback_engine import feedback_engine
    feedback_engine.execute_recalibration(rid)
    return {"status": "success", "recalibration_id": rid}

@router.post("/recalibration/revert")
async def revert_recalibration(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """Reverts an active recalibration."""
    rid = payload.get("recalibration_id")
    from backend.core.governance.feedback_engine import feedback_engine
    feedback_engine.revert_recalibration(rid)
    return {"status": "success", "recalibration_id": rid}

@router.get("/recalibration/parameters")
async def get_governance_parameters(admin_user: OmniUser = Depends(get_admin_user)):
    """Returns all recalibratable parameters of the governance system."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_engine_parameters").fetchall()
            return {"status": "success", "payload": [dict(r) for r in rows]}

# --- OMNIWEB — BLOQUE: GOVERNANCE MULTI-PROJECT CONTEXTUAL MAPPING (PHASE 112) ---

@router.get("/mapping/profile")
async def trigger_contextual_profiling(admin_user: OmniUser = Depends(get_admin_user)):
    """Triggers DNA profiling of the current project and scans for contextual matches."""
    from backend.core.governance.context_mapping_engine import context_mapping_engine
    profile = await context_mapping_engine.profile_current_context()
    matches = await context_mapping_engine.scan_contextual_matches(profile["project_id"])
    return {"status": "success", "profile": profile, "matches": matches}

@router.get("/mapping/list")
async def get_contextual_mappings(project_id: str = "PROJECT_OMNIWEB_PROD", admin_user: OmniUser = Depends(get_admin_user)):
    """Returns past and current contextual mappings for the project."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_contextual_mappings WHERE target_project_id = ?", (project_id,)).fetchall()
            return {"status": "success", "payload": [dict(r) for r in rows]}

@router.post("/mapping/transfer")
async def execute_contextual_transfer(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """Applies contextual baselines from a similarity match to the current project."""
    mapping_id = payload.get("mapping_id")
    keys = payload.get("keys") # Optional list of params
    from backend.core.governance.context_mapping_engine import context_mapping_engine
    await context_mapping_engine.execute_transfer(mapping_id, keys)
    return {"status": "success", "mapping_id": mapping_id}

@router.post("/projects/seed")
async def seed_reference_project(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 112: Seed a reference project profile to simulate similarity detection."""
    name = payload.get("name", "Referencia")
    pid = payload.get("project_id", f"REF_{uuid.uuid4().hex[:6]}")
    domains = payload.get("domains", ["core", "ui"])
    thresholds = payload.get("thresholds", {"FRICTION_THRESHOLD": 50.0})
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("INSERT OR IGNORE INTO governance_projects (project_id, name) VALUES (?, ?)", (pid, name))
            conn.execute("""
                INSERT OR REPLACE INTO governance_project_contexts (
                    context_id, project_id, primary_domains, risk_profile_dna, 
                    learning_density, active_thresholds, confidence, rationale
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                f"CTX_{pid}", pid, json.dumps(domains), json.dumps({"avg_friction": 30.0}),
                5.0, json.dumps(thresholds), 1.0, "Reference profile for similarity testing."
            ))
            conn.commit()
    return {"status": "success", "project_id": pid}

# --- OMNIWEB — BLOQUE: GOVERNANCE CROSS-PROJECT LEARNING SEARCH (PHASE 113) ---

@router.get("/mapping/search")
async def trigger_cross_project_search(domain: str = None, problem_type: str = None, keywords: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 113: Searches for specific learnings/autopsies across all projects."""
    from backend.core.governance.cross_project_search_engine import cross_project_search_engine
    results = await cross_project_search_engine.search_learnings(domain, problem_type, keywords)
    return {"status": "success", "payload": results}

@router.post("/mapping/search/action")
async def register_search_result_action(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """Registers Creator's response to a search result (ADOPTED, IGNORED)."""
    search_id = payload.get("search_id")
    action = payload.get("action")
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE governance_cross_project_search_traces SET creator_action = ? WHERE search_id = ?", (action, search_id))
            conn.commit()
    return {"status": "success", "search_id": search_id, "action": action}

# --- OMNIWEB — BLOQUE: GOVERNANCE TACTICAL REPLAY & SIMULATION (PHASE 301) ---

@router.post("/simulation/run")
async def trigger_tactical_simulation(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 301: Runs a contextual simulation for a reusable learning/tactic."""
    source_type = payload.get("source_type")
    source_id = payload.get("source_id")
    target_domain = payload.get("target_domain")
    
    from backend.core.governance.tactical_simulation_engine import tactical_simulation_engine
    result = await tactical_simulation_engine.run_tactical_simulation(source_type, source_id, target_domain)
    return {"status": "success", "payload": result}

@router.get("/simulation/results")
async def get_simulation_results(simulation_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Retrieves simulation trace by ID."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM governance_tactical_simulations WHERE simulation_id = ?", (simulation_id,)).fetchone()
            if not row: return {"error": "Not found"}
            return {"status": "success", "payload": dict(row)}

# --- OMNIWEB — BLOQUE: GOVERNANCE STRATEGIC REPLAY LEDGER & AUTO-AUTOPSY SYNC (PHASE 401) ---

@router.post("/simulation/sync")
async def trigger_replay_sync(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 401: Synchronizes a simulation prediction with its real outcome (autopsy)."""
    autopsy_id = payload.get("autopsy_id")
    branch_id = payload.get("branch_id")
    
    from backend.core.governance.replay_sync_engine import replay_sync_engine
    res = await replay_sync_engine.synchronize_simulation_outcome(autopsy_id, branch_id)
    return {"status": "success", "payload": res}

@router.get("/simulation/sync/list")
async def get_replay_sync_list(admin_user: OmniUser = Depends(get_admin_user)):
    """Returns the history of oracular alignment (Simulation vs Reality)."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_replay_syncs ORDER BY created_at DESC").fetchall()
            return {"status": "success", "payload": [dict(r) for r in rows]}

@router.post("/simulation/sync/apply")
async def apply_confidence_adjustment(payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """Applies the oracular delta to the source learning's confidence score."""
    sync_id = payload.get("sync_id")
    with set_chip_context("core"):
        async with db_manager.get_session() as session:
            sync_res = await session.execute("SELECT * FROM governance_replay_syncs WHERE sync_id = ?", (sync_id,))
            sync = sync_res.fetchone()
            if not sync: return {"error": "Sync record not found"}
            
            # Find the learning via simulation
            sim_res = await session.execute("SELECT source_object_id FROM governance_tactical_simulations WHERE simulation_id = ?", (sync["simulation_id"],))
            sim = sim_res.fetchone()
            if not sim: return {"error": "Simulation not found"}
            
            # Update learning confidence
            await session.execute(
                "UPDATE governance_learning_items SET confidence = confidence + ? WHERE learning_item_id = ?",
                (sync["confidence_delta_proposed"], sim["source_object_id"])
            )
            # Mark sync as applied
            await session.execute("UPDATE governance_replay_syncs SET creator_action = 'APPLIED' WHERE sync_id = ?", (sync_id,))
            
    return {"status": "success", "sync_id": sync_id}

# --- OMNIWEB — BLOQUE: WISDOM ATLAS UX (ATLAS DE SABIDURÍA / SUPERFICIE DE MEMORIA TÁCTICA) ---

@router.get("/wisdom/atlas/nodes")
async def get_wisdom_atlas_nodes(node_type: str = None, project_id: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: WISDOM ATLAS UX.
    Returns aggregated wisdom nodes for the navigable atlas.
    """
    from backend.core.governance.atlas_engine import atlas_engine
    nodes = atlas_engine.get_nodes(node_type=node_type, project_id=project_id)
    return {"status": "success", "payload": [node.model_dump() for node in nodes]}

@router.post("/wisdom/atlas/refresh")
async def refresh_wisdom_atlas(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: WISDOM ATLAS UX.
    Forces a re-aggregation of all wisdom sources into the atlas.
    """
    from backend.core.governance.atlas_engine import atlas_engine
    atlas_engine.aggregate_all()
    # Fetch again to return the new count
    nodes = atlas_engine.get_nodes()
    return {"status": "success", "message": "Atlas de Sabiduría actualizado con éxito.", "count": len(nodes)}

@router.get("/wisdom/atlas/node/{node_id}")
async def get_wisdom_atlas_node_detail(node_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Returns details and connected evidence for a specific wisdom node."""
    from backend.core.governance.atlas_engine import atlas_engine
    nodes = atlas_engine.get_nodes()
    node = next((n for n in nodes if n.node_id == node_id), None)
    if not node:
        raise HTTPException(status_code=404, detail="Atlas Node not found.")
    return {"status": "success", "payload": node.model_dump()}

# --- OMNIWEB — BLOQUE: WISDOM GRAPH EXPLORER (VISTA DE GRAFO DEL ATLAS DE SABIDURÍA) ---

@router.get("/wisdom/graph/data")
async def get_wisdom_graph_data(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: WISDOM GRAPH EXPLORER.
    Returns nodes and edges for the graph visualization.
    """
    from backend.core.governance.graph_engine import graph_engine
    # Ensure graph is built (could be async or triggered by refresh)
    # For now, return latest data.
    return {"status": "success", "payload": graph_engine.get_graph_data()}

@router.post("/wisdom/graph/refresh")
async def refresh_wisdom_graph(admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: WISDOM GRAPH EXPLORER.
    Rebuilds the graph relationships based on latest atlas nodes.
    """
    from backend.core.governance.graph_engine import graph_engine
    graph_engine.rebuild_graph()
    return {"status": "success", "message": "Grafo de Sabiduría actualizado con éxito."}

# --- OMNIWEB — BLOQUE: TACTICAL WISDOM REASONER (RAZONADOR DE SABIDURÍA TÁCTICA) ---

@router.post("/wisdom/reasoner/analyze")
async def analyze_wisdom_reasoner(context_data: Dict[str, Any], admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: TACTICAL WISDOM REASONER.
    Returns categorized and prioritized wisdom nodes for the current context.
    """
    from backend.core.governance.wisdom_reasoner import wisdom_reasoner
    suggestions = wisdom_reasoner.analyze_context(context_data)
    return {"status": "success", "payload": [s.model_dump() for s in suggestions]}

# --- OMNIWEB — BLOQUE: WISDOM-DRIVEN MISSION AUTO-DRAFT ---

@router.post("/wisdom/drafts/generate")
async def generate_mission_draft(request: Dict[str, Any], admin_user: OmniUser = Depends(get_admin_user)):
    """
    OMNIWEB — BLOQUE: WISDOM-DRIVEN MISSION AUTO-DRAFT.
    Translates a reasoner suggestion into a structured, editable mission draft.
    """
    from backend.core.governance.draft_engine import draft_engine
    suggestion = request.get("suggestion")
    context = request.get("context")
    if not suggestion or not context:
        return {"status": "error", "message": "Falta sugerencia o contexto para generar el draft."}
    
    draft = draft_engine.create_draft_from_suggestion(suggestion, context)
    return {"status": "success", "payload": draft.model_dump()}

# --- OMNIWEB — BLOQUE: TACTICAL WISDOM FEEDBACK LOOP ---

@router.get("/wisdom/feedback")
async def list_wisdom_feedback(status: str = None, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 114: Returns history or filtered wisdom feedback entries."""
    with db_manager.get_connection() as conn:
        query = "SELECT * FROM governance_wisdom_feedback"
        params = []
        if status:
            query += " WHERE creator_decision = ?"
            params.append(status)
        query += " ORDER BY created_at DESC"
        feedbacks = conn.execute(query, params).fetchall()
        return {"status": "success", "payload": [dict(f) for f in feedbacks]}

@router.get("/wisdom/feedback/pending")
async def get_pending_wisdom_feedback(admin_user: OmniUser = Depends(get_admin_user)):
    """Retrieves pending tactical wisdom feedback adjustments for Creator review."""
    with db_manager.get_connection() as conn:
        feedbacks = conn.execute("""
            SELECT * FROM governance_wisdom_feedback 
            WHERE creator_decision = 'PENDING'
            ORDER BY created_at DESC
        """).fetchall()
        return {"status": "success", "payload": [dict(f) for f in feedbacks]}

@router.post("/wisdom/feedback/{feedback_id}/confirm")
async def confirm_wisdom_feedback(feedback_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Confirms and applies a wisdom feedback recalibration to the Atlas."""
    from backend.core.governance.feedback_engine import wisdom_feedback_engine
    success = wisdom_feedback_engine.apply_feedback(feedback_id)
    if success:
        return {"status": "success", "message": "Resumen táctico recalibrado en el Atlas."}
    return {"status": "error", "message": "No se pudo aplicar el feedback (ID inválido o ya procesado)."}

@router.post("/wisdom/feedback/{feedback_id}/reject")
async def reject_wisdom_feedback(feedback_id: str, admin_user: OmniUser = Depends(get_admin_user)):
    """Rejects a proposed wisdom recalibration."""
    from backend.core.governance.feedback_engine import wisdom_feedback_engine
    success = wisdom_feedback_engine.reject_feedback(feedback_id)
    if success:
        return {"status": "success", "message": "Feedback táctico rechazado / ignorado."}
    return {"status": "error", "message": "No se pudo procesar el rechazo (ID inválido o ya procesado)."}

@router.post("/wisdom/bridge/compose")
async def compose_action_package(context_data: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 116: Generates a tactical action package from multiple wisdom nodes."""
    from backend.core.governance.composition_engine import wisdom_action_bridge
    package = wisdom_action_bridge.compose_from_suggestions(context_data)
    if package:
        return {"status": "success", "payload": package.model_dump()}
    return {"status": "error", "message": "No se pudo componer un paquete (insuficiente sabiduría o confianza)."}

@router.get("/wisdom/bridge/packages")
async def list_action_packages(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 116: Returns pending tactical action packages."""
    from backend.core.governance.composition_engine import wisdom_action_bridge
    packages = wisdom_action_bridge.list_pending_packages()
    return {"status": "success", "payload": packages}

@router.post("/wisdom/bridge/package/{package_id}/decision")
async def register_package_decision(package_id: str, payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 116: Creator decision (APPROVED, REJECTED) on a tactical package."""
    decision = payload.get("decision")
    options = payload.get("options", {})
    from backend.core.governance.composition_engine import wisdom_action_bridge
    success = wisdom_action_bridge.process_decision(package_id, decision, options)
    if success:
        return {"status": "success", "message": f"Decisión {decision} registrada."}
    return {"status": "error", "message": "No se pudo registrar la decisión."}

@router.post("/roadmap/optimize")
async def trigger_roadmap_optimization(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 117: Reinterprets all actionable items into a suggested sequence."""
    from backend.core.governance.roadmap_optimizer import roadmap_optimizer
    optimized = roadmap_optimizer.run_full_optimization()
    return {"status": "success", "payload": optimized}

@router.get("/roadmap/optimized")
async def get_optimized_roadmap(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 117: Retrieves the currently suggested tactical sequence."""
    from backend.core.governance.roadmap_optimizer import roadmap_optimizer
    roadmap = roadmap_optimizer.get_current_roadmap()
    return {"status": "success", "payload": roadmap}

@router.patch("/roadmap/item/{item_id}")
async def override_roadmap_item(item_id: str, payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 117: Creator override on a roadmap suggestion (FIXED, IGNORED)."""
    state = payload.get("state")
    from backend.core.governance.roadmap_optimizer import roadmap_optimizer
    success = roadmap_optimizer.update_item_override(item_id, state)
    if success:
        return {"status": "success", "message": f"Estado de roadmap actualizado a {state}."}
    return {"status": "error", "message": "No se pudo actualizar el item."}

@router.get("/roadside/events")
async def list_roadside_events(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 118: Retrieves active roadside tactical warnings."""
    from backend.core.governance.roadside_assistant import roadside_assistant
    events = roadside_assistant.list_active_events()
    return {"status": "success", "payload": events}

@router.post("/roadside/scan")
async def scan_roadside_events(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 118: Explicitly triggers a tactical roadside scan."""
    from backend.core.governance.roadside_assistant import roadside_assistant
    events = roadside_assistant.detect_events()
    return {"status": "success", "payload": events}

@router.post("/roadside/event/{event_id}/action")
async def take_roadside_action(event_id: str, payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 118: Creator decision on a roadside event (ACCEPTED, IGNORED)."""
    decision = payload.get("decision")
    from backend.core.governance.roadside_assistant import roadside_assistant
    success = roadside_assistant.process_event_action(event_id, decision)
    if success:
        return {"status": "success", "message": f"Acción {decision} registrada."}
    return {"status": "error", "message": "No se pudo procesar la acción."}

@router.get("/wisdom/sync/pending")
async def list_pending_syncs(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 119: Retrieves pending post-mission wisdom proposals."""
    from backend.core.governance.post_mission_sync import post_mission_sync_engine
    syncs = post_mission_sync_engine.get_pending_syncs()
    return {"status": "success", "payload": syncs}

@router.post("/wisdom/sync/scan")
async def scan_for_wisdom_syncs(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 119: Explicitly scans for closed missions suitable for sync."""
    from backend.core.governance.post_mission_sync import post_mission_sync_engine
    syncs = post_mission_sync_engine.scan_for_closures()
    return {"status": "success", "payload": syncs}

@router.post("/wisdom/sync/{sync_id}/decision")
async def register_sync_decision(sync_id: str, payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 119: Creator decision (APPROVED, REJECTED) on a wisdom sync proposal."""
    decision = payload.get("decision")
    from backend.core.governance.post_mission_sync import post_mission_sync_engine
    if decision == 'ACCEPTED':
        success = post_mission_sync_engine.apply_sync(sync_id)
    else:
        from backend.core.database import db_manager
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE governance_post_mission_syncs SET creator_decision = ?, updated_at = CURRENT_TIMESTAMP WHERE sync_id = ?", (decision, sync_id))
            conn.commit()
        success = True
    
    if success:
        return {"status": "success", "message": f"Decisión {decision} registrada."}
    return {"status": "error", "message": "No se pudo registrar la decisión."}

@router.get("/wisdom/harvest/pending")
async def list_pending_harvests(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 120: Retrieves pending multi-context wisdom harvest proposals."""
    from backend.core.governance.wisdom_harvester import wisdom_harvester
    harvests = wisdom_harvester.get_pending_harvests()
    return {"status": "success", "payload": harvests}

@router.post("/wisdom/harvest/scan")
async def scan_for_harvests(admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 120: Explicitly scans for across contexts confirm outcomes for harvest."""
    from backend.core.governance.wisdom_harvester import wisdom_harvester
    harvests = wisdom_harvester.scan_harvests()
    return {"status": "success", "payload": harvests}

@router.post("/wisdom/harvest/{harvest_id}/decision")
async def register_harvest_decision(harvest_id: str, payload: dict, admin_user: OmniUser = Depends(get_admin_user)):
    """PHASE 120: Creator decision (APPROVED, REJECTED) on a wisdom harvest proposal."""
    decision = payload.get("decision")
    from backend.core.governance.wisdom_harvester import wisdom_harvester
    if decision == 'ACCEPTED':
        success = wisdom_harvester.apply_promotion(harvest_id)
    else:
        from backend.core.database import db_manager
        with db_manager.get_connection() as conn:
            conn.execute("UPDATE governance_wisdom_harvests SET creator_decision = ?, updated_at = CURRENT_TIMESTAMP WHERE harvest_id = ?", (decision, harvest_id))
            conn.commit()
        success = True
    
    if success:
        return {"status": "success", "message": f"Promoción {decision} registrada."}
    return {"status": "error", "message": "No se pudo registrar la decisión."}
