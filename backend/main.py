from fastapi import FastAPI, Security, Depends, Request
from typing import List, Optional, Dict, Any
from backend.core.auth import get_current_user, OmniUser
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import uvicorn
import sys
import os

from backend.core.config import settings
from backend.core.module_registry import module_registry
from backend.core.database import db_manager
from backend.core.self_check import run_self_checks
from backend.core.permissions import _current_chip_ctx, set_chip_context
from starlette.middleware.base import BaseHTTPMiddleware

from uvicorn.middleware.proxy_headers import ProxyHeadersMiddleware

# --- Initialize Persistence (Phase 42: Boot Priority) ---
with set_chip_context("core"):
    db_manager.init_db()
    db_manager.run_migrations()

# --- Import New Routers ---
from backend.core.auth_router import router as auth_router
from backend.core.system_router import router as system_router
from backend.core.education_engine.router import router as edu_router
from backend.core.ecosystem_router import router as ecosystem_router
from backend.core.human_development_router import router as human_development_router
from backend.core.collaboration_economy.router import router as ecosystem_collab_router
from backend.core.scaling_observability.router import router as scaling_router
from backend.core.knowledge_domains import domain_router
from backend.core.collaboration_spaces import collaboration_router
from backend.core.user_onboarding import onboarding_router
from backend.core.logbook_network import logbook_router
from backend.core.user_context.router import router as context_router
from backend.core.ai_host.routing.router import ai_host_router as aihost_router
from backend.core.stability_loop.router import router as stability_router
from backend.core.master_logbook.router import router as master_logbook_router
from backend.core.identity.router import router as identity_router
from backend.core.security.creator_router import router as creator_gateway_router
from backend.core.user_logbook.router import router as user_logbook_router
from backend.core.user_graph.router import router as user_graph_router
from backend.core.insight_engine.router import router as insight_router
from backend.core.sync.router import router as sync_router
from backend.core.admin_logbook.router import router as admin_router
from backend.core.creator_control.router import router as creator_control_router
from backend.core.cluster.router import router as cluster_router
from backend.core.governance.router import router as governance_router
from backend.core.communication.communication_router import router as communication_router
from backend.core.integration_layer.integration_router import router as integration_router
from backend.core.qr_gateway.qr_gateway_router import router as qr_router
from backend.core.creator_fs.file_system_router import router as creator_fs_router
from backend.core.creator_copilot.router import router as creator_copilot_router

# Ensure the root of the project is in the Python path
sys.path.append(os.getcwd())

run_self_checks()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    root_path=settings.ROOT_PATH
)

# --- Middleware ---
if settings.BACKEND_CORS_ORIGINS:
    # Rule: Browser rejects "*" with credentials. We explicitly list common dev origins or use '*' without credentials.
    # Given Omni's shell uses Bearer tokens (headers) and not cookies, we can disable allow_credentials if using wildcard.
    origins = [str(origin) for origin in settings.BACKEND_CORS_ORIGINS]
    allow_all = "*" in origins
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins if not allow_all else ["*"],
        allow_credentials=not allow_all and settings.ENVIRONMENT == "dev", # Stricter in non-dev
        allow_methods=["*"],
        allow_headers=["*"],
    )

class ChipContextMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        path = request.url.path
        prefix = f"{settings.API_V1_STR}/"
        chip_slug = "core"
        if path.startswith(prefix):
            parts = path[len(prefix):].split("/")
            if parts and parts[0] not in ["system", "health", "auth", "onboarding", "creator", "editor"]:
                chip_slug = parts[0]
        token = _current_chip_ctx.set({"chip_slug": chip_slug, "user_id": None})
        try:
            return await call_next(request)
        finally:
            _current_chip_ctx.reset(token)

app.add_middleware(ChipContextMiddleware)
app.add_middleware(ProxyHeadersMiddleware, trusted_hosts=settings.PROXY_TRUSTED_HOSTS)

# --- Base Routes ---
@app.get("/")
async def root():
    return FileResponse("frontend/shell/index.html")

@app.get("/api/mission/{mission_id}/briefing")
async def get_mission_briefing(mission_id: str):
    """
    CAPA 1 (PHASE 70): STRATEGIC BRIEFING API.
    Provides preventive wisdom for a mission.
    """
    with set_chip_context("core"):
        mission = mission_manager.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        return mission.generate_pre_mission_briefing()

@app.get("/api/mission/{mission_id}/replay")
async def get_mission_replay(mission_id: str):
    """
    CAPA 2 (PHASE 71): FORENSIC REPLAY API.
    Provides a chronological event trace for a mission.
    """
    with set_chip_context("core"):
        mission = mission_manager.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        return mission.generate_cognitive_replay_trace()

@app.get("/api/mission/{mission_id}/simulate")
async def get_mission_simulation(mission_id: str):
    """
    CAPA 2 (PHASE 72): COGNITIVE FORESIGHT API.
    Provides comparative "What-If" scenarios for drift mitigation.
    """
    with set_chip_context("core"):
        mission = mission_manager.get_mission(mission_id)
        if not mission:
            raise HTTPException(status_code=404, detail="Mission not found")
        return mission.generate_mitigation_scenarios()

@app.get("/api/mission/{mission_id}")
async def get_mission_details(mission_id: str):
    return FileResponse("frontend/dashboard/index.html")

@app.get("/api/v1/roadmap/macro")
async def get_macro_roadmap(branch_id: str = "main"):
    """
    OMNIWEB — BLOQUE: COGNITIVE ROADMAP AGGREGATOR.
    Provides a strategic macro view of the system's progress for a specific branch.
    """
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.get_macro_roadmap(branch_id=branch_id)

@app.get("/api/v1/roadmap/preview/{group_id}")
async def get_domain_rebase_preview(group_id: str):
    """
    OMNIWEB — BLOQUE: DOMAIN REBASE PREVIEW.
    Generates an atomic rebase plan for a specific domain.
    """
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.get_domain_preview(group_id)

@app.post("/api/v1/roadmap/push/start/{group_id}")
async def start_atomic_push(group_id: str):
    """
    OMNIWEB — BLOQUE: ATOMIC PUSH EXECUTION.
    Starts a governed push session for a domain.
    """
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.start_push_session(group_id)

@app.get("/api/v1/roadmap/push/{push_id}")
async def get_push_status(push_id: str):
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.get_session(push_id)

@app.post("/api/v1/roadmap/push/{push_id}/next")
async def execute_push_next_step(push_id: str):
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.execute_next_step(push_id)

@app.post("/api/v1/roadmap/push/{push_id}/abort")
async def abort_atomic_push(push_id: str):
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        roadmap_aggregator.abort_push(push_id)
        return {"status": "aborted"}

@app.post("/api/v1/roadmap/push/{push_id}/authority")
async def inject_push_authority(push_id: str, payload: dict):
    """
    OMNIWEB — BLOQUE: AUTHORITY HUD INTEGRATION.
    Injects authority (PIN) into a blocked push session.
    """
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    pin = payload.get("pin")
    if not pin:
        raise HTTPException(status_code=400, detail="Missing PIN")
        
    with set_chip_context("core"):
        try:
            return roadmap_aggregator.inject_authority(push_id, pin)
        except ValueError as e:
            raise HTTPException(status_code=403, detail=str(e))

@app.get("/api/v1/roadmap/push/{push_id}/forensics")
async def get_push_forensics(push_id: str):
    """
    OMNIWEB — BLOQUE: TACTICAL TELEMETRY & FORENSICS.
    Retrieves the historical forensic log of a push session.
    """
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.get_forensics(push_id)

@app.get("/api/v1/roadmap/push/{push_id}/rollback/preview")
async def get_rollback_preview(push_id: str):
    """
    OMNIWEB — BLOQUE: GOVERNED ROLLBACK LOGIC.
    Generates a preview of what can be reverted for a given push.
    """
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.preview_rollback(push_id)

@app.post("/api/v1/roadmap/rollback/{rollback_id}/start")
async def start_rollback(rollback_id: str):
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.start_rollback(rollback_id)

@app.post("/api/v1/roadmap/rollback/{rollback_id}/next")
async def execute_rollback_step(rollback_id: str):
    from backend.core.ai_host.memory.roadmap_aggregator import roadmap_aggregator
    with set_chip_context("core"):
        return roadmap_aggregator.execute_next_rollback_step(rollback_id)

@app.get("/api/v1/roadmap/schedule/{schedule_id}")
async def get_schedule(schedule_id: str):
    from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
    with set_chip_context("core"):
        return scheduler_manager.get_schedule(schedule_id)

@app.post("/api/v1/roadmap/schedule/{schedule_id}/reorder/analyze")
async def analyze_reorder(schedule_id: str, proposed_order: List[str]):
    from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
    with set_chip_context("core"):
        return scheduler_manager.analyze_reorder(schedule_id, proposed_order)

@app.post("/api/v1/roadmap/schedule/{schedule_id}/reorder/apply")
async def apply_reorder(schedule_id: str, proposed_order: List[str]):
    from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
    with set_chip_context("core"):
        scheduler_manager.update_order(schedule_id, proposed_order)
        return {"status": "success", "new_order": proposed_order}

@app.get("/api/v1/roadmap/synergy/analyze")
async def analyze_synergy():
    """
    OMNIWEB — BLOQUE: MISSION SYNERGY & REDUNDANCY PURGE.
    Detects redundancies and synergies in the current backlog.
    """
    from backend.core.ai_host.memory.synergy_manager import synergy_manager
    with set_chip_context("core"):
        return synergy_manager.analyze_backlog()

@app.post("/api/v1/roadmap/synergy/apply")
async def apply_synergy_insight(insight_json: Dict[str, Any]):
    from backend.core.ai_host.memory.synergy_manager import synergy_manager, SynergyInsight
    with set_chip_context("core"):
        insight = SynergyInsight(**insight_json)
        return synergy_manager.apply_insight(insight)

@app.get("/api/v1/roadmap/opportunities/scan")
async def scan_opportunities():
    """
    OMNIWEB — BLOQUE: TACTICAL OPPORTUNITY SCANNER.
    Scans the system for friction patterns and proactive improvements.
    """
    from backend.core.ai_host.memory.opportunity_scanner import opportunity_scanner
    with set_chip_context("core"):
        return opportunity_scanner.scan_for_opportunities()

@app.post("/api/v1/roadmap/opportunities/{opportunity_id}/convert")
async def convert_opportunity(opportunity_id: str):
    from backend.core.ai_host.memory.opportunity_scanner import opportunity_scanner
    with set_chip_context("core"):
        return opportunity_scanner.convert_to_mission(opportunity_id)

@app.get("/api/v1/roadmap/sync/audit")
async def audit_sync():
    """
    OMNIWEB — BLOQUE: CROSS-DOMAIN SYNC AUDITOR.
    Audit connections and readiness dependencies across distinct domains.
    """
    from backend.core.ai_host.memory.sync_auditor import sync_auditor
    with set_chip_context("core"):
        return sync_auditor.audit_cross_domain_sync()

@app.post("/api/v1/roadmap/sync/{relation_id}/suggest")
async def suggest_sync_mission(relation_id: str):
    from backend.core.ai_host.memory.sync_auditor import sync_auditor
    from backend.core.ai_host.memory.handoff_manager import handoff_manager
    with set_chip_context("core"):
        suggestion = sync_auditor.get_coordination_mission_suggestion(relation_id)
        if suggestion:
            mission = handoff_manager.add_proposal(suggestion, source="sync_auditor")
            return mission.model_dump()
        return {"error": "Relation not found"}

@app.get("/api/v1/handoffs/{id}/audit")
async def audit_mission(id: str):
    """
    OMNIWEB — BLOQUE: CONSTITUTIONAL SELF-AUDIT SUITE.
    Audits a proposed mission against the system constitution.
    """
    from backend.core.ai_host.memory.handoff_manager import handoff_manager
    from backend.core.ai_host.memory.constitutional_auditor import constitutional_auditor
    with set_chip_context("core"):
        mission = handoff_manager.get_proposal(id)
        if not mission: return {"error": "Mission not found"}
        return constitutional_auditor.audit_mission(mission).model_dump()

@app.post("/api/v1/handoffs/{id}/fix_branding")
async def fix_mission_branding(id: str):
    from backend.core.ai_host.memory.handoff_manager import handoff_manager
    with set_chip_context("core"):
        mission = handoff_manager.get_proposal(id)
        if not mission: return {"error": "Mission not found"}
        
        # Automatic correction of 'OmniShell' for branding compliance
        import re
        mission.objective = re.sub(r'OmniShell', 'OmniWeb', mission.objective, flags=re.IGNORECASE)
        mission.briefing_title = re.sub(r'OmniShell', 'OmniWeb', mission.briefing_title, flags=re.IGNORECASE)
        
        handoff_manager.update_proposal(id, mission.model_dump())
        return {"status": "success", "new_objective": mission.objective}

@app.get("/api/v1/personas")
async def get_personas():
    from backend.core.ai_host.memory.persona_sync import persona_sync
    return {k: v.model_dump() for k, v in persona_sync.personas.items()}

@app.get("/api/v1/personas/conflicts")
async def get_vision_conflicts():
    from backend.core.ai_host.memory.persona_sync import persona_sync
    with set_chip_context("core"):
        conflicts = persona_sync.detect_vision_conflicts()
        return [c.model_dump() for c in conflicts]

@app.post("/api/v1/personas/conflicts/{id}/arbitrate")
async def arbitrate_vision_conflict(id: str):
    from backend.core.ai_host.memory.persona_sync import persona_sync
    with set_chip_context("core"):
        return persona_sync.arbitrate_by_constitution(id)

@app.post("/api/v1/handoffs/{id}/persona")
async def set_mission_persona(id: str, persona: str):
    from backend.core.ai_host.memory.handoff_manager import handoff_manager
    with set_chip_context("core"):
        mission = handoff_manager.get_proposal(id)
        if not mission: return {"error": "Mission not found"}
        mission.origin_persona = persona
        handoff_manager.update_proposal(id, mission.model_dump())
        return {"status": "success", "origin_persona": persona}

# Note: get_macro_roadmap moved to top for organization

@app.get("/api/v1/governance/debt/cockpit")
async def get_governance_debt_cockpit(current_user: OmniUser = Depends(get_current_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE DEBT COCKPIT.
    Returns a unified view of structural risk overrides, pressure, and degradation.
    """
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        enforce_permission("creator_access")
        dashboard = branch_manager.get_accepted_debt_dashboard()
        return dashboard

@app.get("/api/v1/governance/fusion/{target_id}")
async def get_governance_fusion(target_id: str, target_type: str = 'MISSION', current_user: OmniUser = Depends(get_current_user)):
    """
    OMNIWEB — BLOQUE: GOVERNANCE FUSION ENDPOINT.
    Returns a composite governance snapshot for a mission, domain or handoff.
    """
    from backend.core.ai_host.observability.governance_fusion_engine import fusion_engine
    from backend.core.permissions import enforce_permission
    with set_chip_context("core"):
        enforce_permission("creator_access")
        snapshot = fusion_engine.get_fusion_snapshot(target_id, target_type)
        return snapshot

@app.get("/api/v1/roadmap/simulate")
async def simulate_roadmap(branch_id: str = "main"):
    """
    OMNIWEB — BLOQUE: STRATEGIC SIMULATION MODE.
    Projects future roadmaps and friction.
    """
    from backend.core.ai_host.memory.strategic_sim import strategic_simulator
    with set_chip_context("core"):
        scenarios = strategic_simulator.generate_scenarios(branch_id=branch_id)
        return [s.model_dump() for s in scenarios]

@app.get("/api/v1/roadmap/branches/{id}/dossier")
async def get_branch_dossier(id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_branch_dossier(id)

@app.post("/api/v1/roadmap/branches/{id}/arbitrate")
async def apply_arbitration(id: str, data: dict):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.apply_arbitration_decision(
            id, data["decision"], data["rationale"], data.get("conditions", [])
        )

@app.get("/api/v1/roadmap/exceptions/{id}/recovery")
async def get_recovery_proposals(id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        proposals = branch_manager.generate_recovery_proposals(id)
        return [p.model_dump() for p in proposals]

@app.post("/api/v1/roadmap/recovery/inject")
async def inject_recovery(data: dict):
    from backend.core.ai_host.memory.branch_manager import branch_manager, RecoveryProposal
    proposal = RecoveryProposal(**data)
    with set_chip_context("core"):
        return branch_manager.apply_recovery_proposal(proposal)

@app.get("/api/v1/roadmap/oracle/{type}/{id}")
async def get_health_oracle(type: str, id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        forecasts = branch_manager.project_constitutional_health(id, type)
        return [f.model_dump() for f in forecasts]

@app.get("/api/v1/roadmap/exceptions-report")
async def get_exceptions_report():
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_exceptions_report()

@app.post("/api/v1/roadmap/exceptions/{id}/resolve")
async def resolve_exception(id: str, data: dict):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.resolve_exception(id, data.get("state", "FULFILLED"))

@app.get("/api/v1/roadmap/healing/proposals")
async def get_healing_proposals():
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return [p.model_dump() for p in branch_manager.generate_healing_packages()]

@app.post("/api/v1/roadmap/healing/apply")
async def apply_healing(payload: Dict[str, Any]):
    from backend.core.ai_host.memory.branch_manager import branch_manager, HealingPackage
    pkg = HealingPackage(**payload["package"])
    with set_chip_context("core"):
        return branch_manager.apply_healing_actions(payload["action_ids"], pkg)

@app.get("/api/v1/roadmap/pruning/candidates")
async def get_pruning_candidates():
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return [c.model_dump() for c in branch_manager.get_pruning_candidates()]

@app.post("/api/v1/roadmap/pruning/apply")
async def apply_pruning(payload: Dict[str, Any]):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.archive_signals(payload["signal_ids"])

@app.get("/api/v1/governance/pre-mission-check/{target_id}")
async def pre_mission_check(target_id: str, type: str = "PROPOSAL"):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        check = branch_manager.perform_pre_mission_check(target_id, type)
        return check.model_dump()

@app.post("/api/v1/governance/pre-mission-check/{check_id}/decision")
async def register_pre_mission_decision(check_id: str, data: dict):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        success = branch_manager.register_precheck_decision(check_id, data["decision"])
        return {"status": "success" if success else "error"}

@app.get("/api/v1/governance/debt/cockpit")
async def get_debt_cockpit():
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_accepted_debt_dashboard()

@app.post("/api/v1/roadmap/advisory/accept")
async def accept_advisory(payload: Dict[str, Any]):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.accept_governance_advisory(payload["advisory_id"])

@app.get("/api/v1/roadmap/advisory/dashboard")
async def get_advisory_dashboard():
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_governance_advisory_dashboard()

@app.get("/api/v1/roadmap/advisory/rebase-recommendations")
async def get_rebase_recommendations(branch_id: str = "main"):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_mission_rebase_recommendations(branch_id=branch_id)

@app.post("/api/v1/roadmap/advisory/rebase-recommendations/{id}/action")
async def update_rebase_recommendation(id: str, payload: dict):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    state = payload.get("state")
    if not state: raise HTTPException(status_code=400, detail="Missing state")
    with set_chip_context("core"):
        return branch_manager.update_rebase_recommendation(id, state)

@app.get("/api/v1/roadmap/advisory/rebase-recommendations/{id}/preview")
async def get_rebase_recommendation_preview(id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        preview = branch_manager.get_rebase_recommendation_preview(id)
        if not preview: raise HTTPException(status_code=404, detail="Recommendation not found")
        return preview

@app.post("/api/v1/roadmap/advisory/risk-override")
async def apply_risk_override(payload: dict):
    from backend.core.ai_host.memory.branch_manager import branch_manager, RiskOverride
    from datetime import datetime
    
    # Simple mapping
    override = RiskOverride(
        recommendation_id=payload["recommendation_id"],
        target_id=payload["target_id"],
        override_type=payload.get("override_type", "ACCEPTED_RISK"),
        risk_level=payload["risk_level"],
        rationale=payload["rationale"],
        conditions=payload.get("conditions"),
        expiry_at=datetime.fromisoformat(payload["expiry_at"]) if payload.get("expiry_at") else None
    )
    
    with set_chip_context("core"):
        return branch_manager.apply_risk_override(override)

@app.get("/api/v1/roadmap/advisory/accepted-debt")
async def get_accepted_debt_dashboard():
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_accepted_debt_dashboard()

@app.post("/api/v1/roadmap/advisory/risk-override/{id}/review")
async def review_risk_override(id: str, payload: dict):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    decision = payload.get("decision") # RENEW, CLOSE, ESCALATE
    rationale = payload.get("rationale")
    if not decision or not rationale: raise HTTPException(status_code=400, detail="Missing decision or rationale")
    
    with set_chip_context("core"):
        return branch_manager.review_risk_override(id, decision, rationale)

@app.get("/api/v1/roadmap/pressure-timeline/{id}")
async def get_pressure_timeline(id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_pressure_timeline(id).model_dump()

@app.get("/api/v1/roadmap/forensics/{id}/replay")
async def get_forensics_replay(id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_forensics_replay(id).model_dump()

@app.get("/api/v1/roadmap/strategic-dashboard")
async def get_strategic_dashboard():
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.get_strategic_dashboard()

@app.get("/api/v1/roadmap/branches")
async def list_branches():
    from backend.core.ai_host.memory.branch_manager import branch_manager
    return [b.model_dump() for b in branch_manager.get_branches()]

@app.post("/api/v1/roadmap/branches")
async def create_branch(name: str, origin: str = "main", branch_type: str = "tactical"):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.create_branch(name, origin=origin, branch_type=branch_type).model_dump()

@app.get("/api/v1/roadmap/branches/{id}/diff")
async def get_branch_diff(id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    diff = branch_manager.compare_with_main(id)
    if not diff: raise HTTPException(status_code=404, detail="Branch not found")
    return diff.model_dump()

@app.get("/api/v1/roadmap/branches/{id}/persona-sim")
async def get_branch_persona_sim(id: str):
    from backend.core.ai_host.memory.persona_simulator import persona_simulator
    sim = persona_simulator.simulate_branch_reaction(id)
    if not sim: raise HTTPException(status_code=404, detail="Branch not found")
    return sim.model_dump()

@app.post("/api/v1/roadmap/branches/{id}/merge")
async def merge_branch(id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    return branch_manager.merge_branch(id)

@app.post("/api/v1/roadmap/branches/{id}/compensations/{comp_id}/inject")
async def inject_compensation(id: str, comp_id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.inject_compensation(id, comp_id)

@app.post("/api/v1/roadmap/branches/{id}/compensations/{mission_id}/revert")
async def revert_compensation(id: str, mission_id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    with set_chip_context("core"):
        return branch_manager.revert_compensation(id, mission_id)

@app.delete("/api/v1/roadmap/branches/{id}")
async def discard_branch(id: str):
    from backend.core.ai_host.memory.branch_manager import branch_manager
    branch_manager.delete_branch(id)
    return {"status": "discarded", "branch_id": id}

@app.get("/dashboard")
async def dashboard():
    return FileResponse("frontend/dashboard/index.html")

# --- Include Modular Routers ---
app.include_router(auth_router, prefix=f"{settings.API_V1_STR}/auth", tags=["auth"])
app.include_router(identity_router, prefix=f"{settings.API_V1_STR}/auth", tags=["identity"])
app.include_router(creator_gateway_router, prefix=f"{settings.API_V1_STR}/creator", tags=["security-fortress"])
app.include_router(system_router, prefix=f"{settings.API_V1_STR}/system", tags=["system"])
app.include_router(edu_router, prefix=f"{settings.API_V1_STR}/education", tags=["education"])
app.include_router(ecosystem_router, prefix=f"{settings.API_V1_STR}/ecosystem", tags=["ecosystem"])
app.include_router(human_development_router, prefix=f"{settings.API_V1_STR}/human", tags=["human"])
app.include_router(ecosystem_collab_router, prefix=f"{settings.API_V1_STR}/ecosystem_collab", tags=["ecosystem-collab"])
app.include_router(scaling_router, prefix=f"{settings.API_V1_STR}/scaling", tags=["scaling-beta"])
app.include_router(domain_router, prefix=f"{settings.API_V1_STR}/domains", tags=["domains"])
app.include_router(collaboration_router, prefix=f"{settings.API_V1_STR}/collab", tags=["collaboration"])
app.include_router(onboarding_router, prefix=f"{settings.API_V1_STR}/onboarding", tags=["onboarding"])
app.include_router(user_logbook_router, prefix=f"{settings.API_V1_STR}/logbook", tags=["user-logbook"])
app.include_router(user_graph_router, prefix=f"{settings.API_V1_STR}/user/graph", tags=["user-graph"])
app.include_router(insight_router, prefix=f"{settings.API_V1_STR}/user/insights", tags=["insights"])
app.include_router(sync_router, prefix=f"{settings.API_V1_STR}/system/sync", tags=["sync"])
app.include_router(admin_router, prefix=f"{settings.API_V1_STR}/system/admin", tags=["admin"])
app.include_router(creator_control_router, prefix=f"{settings.API_V1_STR}/creator/control", tags=["creator-control"])
app.include_router(creator_fs_router, prefix=f"{settings.API_V1_STR}/creator/fs", tags=["creator-fs"])
app.include_router(creator_copilot_router, prefix=f"{settings.API_V1_STR}/creator/copilot", tags=["creator-copilot"])

# MISSION RESTORE: Explicitly bind the Core Editor Router (Used by editor.js)
from backend.core.ai_host.execution.editor_router import router as core_editor_router
app.include_router(core_editor_router, prefix=f"{settings.API_V1_STR}/editor", tags=["editor"])
app.include_router(cluster_router, prefix=f"{settings.API_V1_STR}/system/cluster", tags=["cluster"])
app.include_router(governance_router, prefix=f"{settings.API_V1_STR}/governance", tags=["governance"])
app.include_router(communication_router, prefix=f"{settings.API_V1_STR}/communication", tags=["communication"])
app.include_router(logbook_router, prefix=f"{settings.API_V1_STR}/logbook-network", tags=["logbook"])
app.include_router(context_router, prefix=f"{settings.API_V1_STR}/user", tags=["user"])
app.include_router(aihost_router, prefix=f"{settings.API_V1_STR}/ai-host", tags=["ai-host"])
app.include_router(stability_router, prefix=f"{settings.API_V1_STR}/system/loop", tags=["stability"])
app.include_router(master_logbook_router, prefix=f"{settings.API_V1_STR}/system/logbook", tags=["master-logbook"])
app.include_router(integration_router, prefix=f"{settings.API_V1_STR}/integration", tags=["integration"])
app.include_router(qr_router, prefix=f"{settings.API_V1_STR}/qr", tags=["qr-gateway"])

# --- AI Host & Other Core Logic ---
# Note: AI Host router is usually included within its own module, 
# ensuring main.py stays clean.

@app.on_event("startup")
async def startup_event():
    # Security Check
    if not settings.IS_ADMIN_TOKEN_SAFE or not settings.IS_CREATOR_PIN_SAFE:
        print("\n" + "!"*60)
        print("WARNING: Using default INSECURE OMNIWEB_ADMIN_TOKEN or PIN.")
        print(f"ENVIRONMENT: {settings.ENVIRONMENT}")
        print("THIS IS INSECURE FOR STAGING/PRODUCTION ENVIRONMENTS.")
        print("!"*60 + "\n")

    with set_chip_context("core"):
        # Phase 28: Initializing Bootable Runtime (Orchestrates all sub-services)
        from backend.core.omni_runtime.runtime_controller import runtime_controller
        await runtime_controller.initialize()
        
        # Phase  integration: Connecting all domains
        from backend.core.integration_layer import start_integration_layer
        await start_integration_layer()

# Initialize Persistence (Already done at boot)

# --- Dynamic Chip Loading (Plugin System) ---
all_chips = module_registry.discover_all_chips()
for chip_metadata in all_chips:
    module_name = chip_metadata["slug"]
    if not chip_metadata.get("active", True):
        continue
    
    # Mount UI
    chip_folder = f"chip-{module_name}"
    ui_path = f"chips/{chip_folder}/frontend"
    if os.path.exists(ui_path):
        app.mount(f"/{module_name}", StaticFiles(directory=ui_path, html=True), name=f"{module_name}_ui")
    
    # Register API Router
    # --- Dynamic Router Isolation (Phase 0 Stabilization) ---
    possible_routers = [
        (f"chips/chip-{module_name}/core/router.py", f"chips.chip-{module_name}.core.router"),
        (f"chips/chip-{module_name}/backend/router.py", f"chips.chip-{module_name}.backend.router")
    ]
    
    found_import_path = None
    for file_path, import_path in possible_routers:
        if os.path.exists(file_path):
            found_import_path = import_path
            break
            
    if found_import_path:
        # Failsafe registration: ensures one bad chip doesn't stall startup
        try:
            module_registry.register_module(
                app=app,
                module_name=module_name,
                router_import_path=found_import_path,
                prefix=f"{settings.API_V1_STR}/{module_name}"
            )
        except Exception as e:
            # High-isolation fail: even if registration crashes (e.g. SyntaxError in chip),
            # we record its existence to satisfy front-end heartbeats.
            module_registry._register_module_state(module_name, None, chip_metadata)
            print(f"CRITICAL: Failed to register chip '{module_name}': {e}")
    elif chip_metadata.get("has_backend"):
         # Record as inactive backend to avoid false "core connection error"
         # by ensuring metadata is at least registered in the modules dict.
         module_registry._register_module_state(module_name, None, chip_metadata)
         print(f"WARNING: Chip '{module_name}' claims backend but no router.py found.")
    else:
         # Explicitly register frontend-only chips to satisfy auditor and health checks
         module_registry._register_module_state(module_name, None, chip_metadata)

app.mount("/shell", StaticFiles(directory="frontend/shell", html=True), name="shell_static")
app.mount("/dashboard-static", StaticFiles(directory="frontend/dashboard"), name="dashboard_static")
app.mount("/workspace", StaticFiles(directory="workspace", html=True), name="workspace_static")
app.mount("/core", StaticFiles(directory="core"), name="core_static")

# Lingua & Global Outputs (Hardened for Staging)
if not os.path.exists("outputs"): os.makedirs("outputs")
app.mount("/outputs", StaticFiles(directory="outputs"), name="outputs_static")

if __name__ == "__main__":
    is_dev = settings.ENVIRONMENT == "dev"
    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000, reload=is_dev)
