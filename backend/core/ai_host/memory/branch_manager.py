import sqlite3
import logging
import uuid
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timedelta
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.handoff_manager import handoff_manager, ProposedMission
from backend.core.ai_host.memory.scheduler_manager import scheduler_manager
from backend.core.ai_host.observability.governance_trace_engine import trace_engine
from backend.core.governance.ledger_engine import governance_ledger_engine

logger = logging.getLogger(__name__)

class RoadmapBranch(BaseModel):
    branch_id: str
    name: str
    origin_branch_id: str = "main"
    branch_type: str = "tactical"
    base_snapshot_id: Optional[str] = None
    branch_state: str = "ACTIVE" # ACTIVE, SIMULATED, MERGED, DISCARDED
    branch_owner_persona: str = "CREATOR_CORE"
    
    # Strategic Metadata
    divergence_score: float = 0.0
    simulation_summary: Optional[Dict[str, Any]] = None
    merge_readiness: float = 0.0
    constitutional_status: str = "PENDING"
    persona_verdict: Optional[str] = None
    
    # Arbitration Trace
    arbitration_id: Optional[str] = None
    is_arbitrated: bool = False
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

    @classmethod
    def from_row(cls, row: Dict[str, Any]):
        data = dict(row)
        if data.get("simulation_summary"):
            try:
                data["simulation_summary"] = json.loads(data["simulation_summary"])
            except: 
                data["simulation_summary"] = {}
        return cls(**data)

class DiffItem(BaseModel):
    ancestry_id: str
    type: str # ADDED, REMOVED, MODIFIED, REORDERED
    title: str
    delta_details: List[str] = []
    level: str = "mission" # mission, domain, governance
    old_value: Optional[Any] = None
    new_value: Optional[Any] = None

class SnapshotDiff(BaseModel):
    diff_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source_branch: str
    target_branch: str
    items: List[DiffItem] = []
    
    # Deltas
    friction_delta: float = 0.0
    readiness_delta: float = 0.0
    risk_delta: float = 0.0
    constitutional_delta: str = "NEUTRAL" # IMPROVED, DEGRADED, NEUTRAL
    
    persona_verdict: Optional[Dict[str, Any]] = None
    compensation_audits: List[Dict[str, Any]] = []
    
    summary: str = ""
    generated_at: datetime = Field(default_factory=datetime.now)

class BranchStrategicSummary(BaseModel):
    branch_id: str
    name: str
    status: str # MERGE_READY, MERGE_READY_WITH_WARNING, NEEDS_COMPENSATION, BLOCKED, DISCARD_CANDIDATE, PENDING
    
    # Core Metrics
    readiness: float
    friction: float
    divergence: float
    constitutional_status: str
    
    # Detailed Signals
    persona_verdict_state: str
    compensation_effect_summary: str # E.g. "2 effective, 1 insufficient"
    unresolved_blockers_count: int
    recommendation: str # PRIORITIZE_MERGE, ITERATE, COMPENSATE, DISCARD, ESCALATE
    rationale: str
    drift_alerts: List[Dict[str, Any]] = []
    last_updated: datetime

class StrategicDashboard(BaseModel):
    dashboard_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    active_branches: List[BranchStrategicSummary]
    focus_recommendation: str # Overall advice for the creator
    generated_at: datetime = Field(default_factory=datetime.now)

class ArbitrationRecord(BaseModel):
    arbitration_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    branch_id: str
    escalation_reason: str = "STRATEGIC_CONFLICT"
    decision: str # APPROVE_ANYWAY, APPROVE_WITH_CONDITIONS, etc.
    rationale: str
    conditions: List[str] = []
    compliance_state: str = "PENDING"
    debt_level: float = 1.0
    created_at: datetime = Field(default_factory=datetime.now)
    resolved_at: Optional[datetime] = None

class BranchDossier(BaseModel):
    branch: RoadmapBranch
    diff: SnapshotDiff
    compensation_audits: List[Dict[str, Any]]
    persona_friction_map: Dict[str, float]
    recommendation: str
    generated_at: datetime = Field(default_factory=datetime.now)

class ConstitutionalException(BaseModel):
    exception_id: str
    branch_id: str
    decision: str
    rationale: str
    conditions: List[str] = []
    compliance_state: str = "PENDING"
    debt_level: float = 1.0
    created_at: datetime
    resolved_at: Optional[datetime] = None
    branch_name: str = ""
    triage: Optional[str] = None

class RecoveryProposal(BaseModel):
    proposal_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    exception_id: str
    debt_type: str
    proposed_mission_type: str
    suggested_objective: str
    suggested_constraints: List[str] = []
    suggested_risk: str = "LOW"
    target_domain: str
    rationale: str
    expected_debt_reduction: float = 0.5


class DriftAlert(BaseModel):
    drift_alert_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source_branch_id: str
    linked_exception_id: str
    drift_type: str # EXCEPTION_REACTIVATION, DEBT_DUPLICATION, DOMAIN_RELAPSE
    severity: str # WARNING, CRITICAL
    affected_domain: str
    rationale: str
    suggested_action: str
    created_at: datetime = Field(default_factory=datetime.now)

class ConstitutionalForecast(BaseModel):
    scenario: str # DO_NOTHING, SANAR_AHORA, ACEPTAR_DERIVA
    debt_score: float
    domain_fragility: float
    governance_load: float
    confidence: float
    rationale: str
    recommendation: str

class TriageRecord(BaseModel):
    source_id: str
    classification: str # CRITICAL_DEBT, MEDIUM_PRIORITY, LOW_IMPACT, SIGNAL_NOISE
    impact_score: float
    persistence: int
    rationale: str
    is_grouped: bool = False

class HealingAction(BaseModel):
    action_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    objective: str
    target_domain: str
    risk_level: str = "LOW"
    rationale: str
    involved_signal_ids: List[str]

class HealingPackage(BaseModel):
    package_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    name: str # CLEANUP_BATCH, etc.
    signals: List[str] # List of exception_ids
    proposed_actions: List[HealingAction]
    total_impact_reduction: float
    rationale: str
    created_at: datetime = Field(default_factory=datetime.now)

class RecurrenceRisk(BaseModel):
    recurrence_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    signal_id: str
    recurrence_state: str # STABLE, FRAGILE, RECURRENT, CRITICAL
    recurrence_count: int
    structural_risk_score: float # 0.0 to 1.0 (1.0 = repair needed)
    archive_permission: bool = True
    confidence: float
    rationale: str
    next_required_action: str # MONITOR, RECOVERY, STRUCTURAL_REVIEW

class PruningCandidate(BaseModel):
    candidate_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    signal_id: str
    branch_name: str
    candidate_type: str # STABLE, HEALED, STALE, RECURRENT_GATED
    stability_score: float 
    structural_risk_score: float = 0.0
    archive_permission: bool = True
    drift_clearance: bool
    archive_reason: str
    created_at: datetime 

class PatternMatch(BaseModel):
    pattern_id: str
    signal_id: str # The matching signal
    match_type: str # STRONG, POSSIBLE, WEAK
    confidence: float
    rationale: str

class GovernancePattern(BaseModel):
    pattern_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    linked_signal_ids: List[str]
    affected_domains: List[str]
    repeated_keywords: List[str]
    structural_risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    confidence: float
    rationale: str
    cluster_state: str = "ACTIVE" # ACTIVE, RESOLVED, ARCHIVED
    first_detected: datetime = Field(default_factory=datetime.now)
    last_detected: datetime = Field(default_factory=datetime.now)

class RebaseRecommendation(BaseModel):
    recommendation_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source_advisory_id: str
    affected_handoff_id: str
    affected_domain: str
    recommendation_state: str = "PENDING" # PENDING, REVIEWED, ACCEPTED, IGNORED, POSTPONED
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    suggested_action: str # REBASE_RECOMMENDED, REVIEW_BEFORE_CONTINUE, FREEZE_UNTIL_RECOVERY, SAFE_TO_CONTINUE
    rationale: str
    confidence: float
    creator_action_required: bool = True
    freshness: datetime = Field(default_factory=datetime.now)

class RebasePreviewOption(BaseModel):
    option_id: str # CONTINUE_AS_IS, REVIEW_BEFORE_CONTINUE, REBASE_RECOMMENDED, FREEZE_UNTIL_RECOVERY
    label: str
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    tactical_cost: str # LOW, MEDIUM, HIGH (Time/Context cost)
    expected_benefit: str # Potential debt reduction
    rationale: str
    is_recommended: bool = False

class RebasePreview(BaseModel):
    preview_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    recommendation_id: str
    source_advisory_id: str
    target_id: str # handoff_id or mission_id
    target_title: str
    affected_domain: str
    current_risk_state: str
    options: List[RebasePreviewOption]
    final_recommendation: str
    confidence: float
    generated_at: datetime = Field(default_factory=datetime.now)

class GovernancePressureEvent(BaseModel):
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_id: str
    event_type: str # PRESSURE_DETECTED, PRESSURE_ESCALATED, PRESSURE_OVERRIDDEN, DEBT_DEGRADED, DEBT_REVIEWED
    source_advisory_id: str
    risk_level: str
    creator_decision: Optional[str] = None # IGNORED, OVERRIDDEN, REBASED, FROZEN
    rationale: str
    timestamp: datetime = Field(default_factory=datetime.now)
    # Lifecycle metadata
    debt_state: Optional[str] = "ACTIVE"
    review_due_at: Optional[datetime] = None

class PressureTimeline(BaseModel):
    target_id: str
    events: List[GovernancePressureEvent]
    first_detected_at: datetime
    duration_hours: float
    current_status: str
    trajectory: str # TEMPORARY_ALERT, PERSISTENT_PRESSURE, ESCALATING_PRESSURE, etc.
    summary: str

class RiskOverride(BaseModel):
    override_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    recommendation_id: str
    target_id: str
    override_type: str # ACCEPTED_RISK, CONDITIONAL, TEMPORARY
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    rationale: str
    affected_domain: Optional[str] = "Global"
    source_advisory_id: Optional[str] = None
    conditions: Optional[str] = None
    expiry_at: Optional[datetime] = None
    created_at: datetime = Field(default_factory=datetime.now)
    # Lifecycle Tracking
    debt_state: str = "ACTIVE" # ACTIVE, STABLE, REVIEW_DUE, OVERDUE, DEGRADED, CLOSED
    review_at: Optional[datetime] = None
    last_reviewed_at: Optional[datetime] = None
    degradation_score: float = 0.0
    oracle_pressure_delta: float = 0.0
    next_required_action: Optional[str] = None
    priority_rank: int = 0
    stability_metrics: Optional[str] = None # JSON metadata

class GovernanceAdvisory(BaseModel):
    advisory_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    source_pattern_id: str
    advisory_state: str = "PENDING" # PENDING, ACCEPTED, DISMISSED, POSTPONED
    advisory_type: str # STRUCTURAL_REFACTOR, DOMAIN_HARDENING, SYSTEM_CLEANUP
    confidence: float
    structural_risk_level: str
    affected_domains: List[str]
    proposed_objective: str
    proposed_constraints: List[str]
    expected_debt_reduction: float
    rationale: str
    created_at: datetime = Field(default_factory=datetime.now)

class ForensicsEvent(BaseModel):
    event_type: str # CREATED, ARBITRATED, RECOVERY, HEALING, ARCHIVED, REACTIVATED
    timestamp: datetime
    title: str
    description: str
    debt_impact: float = 0.0
    link_id: Optional[str] = None # ID of the related mission/package

class ForensicsReplay(BaseModel):
    target_id: str
    events: List[ForensicsEvent]
    trajectory: str # STABILIZING, RESOLVING, RECURRENT_DRIFT, STRUCTURAL_REVIEW, ARCHIVED
    current_debt: float
    total_recurrence: int = 0
    recurrence_risk: Optional[RecurrenceRisk] = None
    summary: str

class ExceptionsReport(BaseModel):
    active_exceptions: List[ConstitutionalException]
    resolved_exceptions: List[ConstitutionalException]
    memory_clusters: List[GovernancePattern] = []
    advisories: List[GovernanceAdvisory] = []
    total_debt_score: float
    report_generated_at: datetime = Field(default_factory=datetime.now)

class PreMissionCheckSignal(BaseModel):
    type: str # DEBT, PRESSURE, ADVISORY, REBASE, FRAGILITY, CONSTITUTION
    severity: str # INFO, WARNING, CRITICAL
    source_id: str
    message: str
    impact_score: float = 0.0

class PreMissionCheck(BaseModel):
    check_id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    target_id: str
    target_type: str # PROPOSAL, MISSION, PUSH
    branch_id: str = "main"
    
    status: str # SAFE_TO_START, START_WITH_WARNING, REVIEW_REQUIRED, REBASE_RECOMMENDED, FREEZE_UNTIL_RECOVERY, ESCALATE_TO_CREATOR_CORE
    
    signals: List[PreMissionCheckSignal] = []
    
    # Aggregated Counters
    active_overdue_debt: int = 0
    degraded_debt: int = 0
    critical_advisory_overlap: int = 0
    rebase_pending: bool = False
    is_constitutionally_valid: bool = True
    
    rationale: str
    confidence: float = 1.0
    suggested_action: str
    created_at: datetime = Field(default_factory=datetime.now)

class BranchManager:
    """
    OMNIWEB — BLOQUE: MISSION EVOLUTION & BRANCHING.
    Manages tactical branches for roadmap experimentation.
    """
    
    def create_branch(self, name: str, origin: str = "main", branch_type: str = "tactical") -> RoadmapBranch:
        branch_id = f"br_{str(uuid.uuid4())[:8]}"
        branch = RoadmapBranch(
            branch_id=branch_id, 
            name=name, 
            origin_branch_id=origin,
            branch_type=branch_type,
            base_snapshot_id=f"snap_{str(uuid.uuid4())[:6]}"
        )
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Create branch metadata
                conn.execute("""
                    INSERT INTO roadmap_branches (
                        branch_id, name, origin_branch_id, branch_type, 
                        base_snapshot_id, branch_state, branch_owner_persona
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    branch.branch_id, branch.name, branch.origin_branch_id, 
                    branch.branch_type, branch.base_snapshot_id, 
                    branch.branch_state, branch.branch_owner_persona
                ))
                
                # 2. Clone missions from origin to the new branch and keep a mapping
                missions = handoff_manager.get_all(branch_id=origin, conn=conn)
                handoff_id_map = {}
                for m in missions:
                    old_id = m.handoff_id
                    new_m = m.model_copy()
                    new_m.handoff_id = str(uuid.uuid4())
                    new_m.branch_id = branch_id
                    handoff_id_map[old_id] = new_m.handoff_id
                    
                    conn.execute("""
                        INSERT INTO mission_handoffs (
                            handoff_id, briefing_title, objective, surface_affected, 
                            constraints, risk_level, execution_style, readiness_state, 
                            source_type, gate_data, foreclosure, priority, origin_persona, 
                            supporting_personas, branch_id, ancestry_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_m.handoff_id, new_m.briefing_title, new_m.objective,
                        json.dumps(new_m.surface_affected), json.dumps(new_m.constraints),
                        new_m.risk_level, new_m.execution_style, new_m.readiness_state,
                        new_m.source_type, json.dumps(new_m.gate_data) if new_m.gate_data else None,
                        json.dumps(new_m.foreclosure.model_dump()),
                        new_m.priority, new_m.origin_persona, json.dumps(new_m.supporting_personas),
                        new_m.branch_id, new_m.ancestry_id or old_id
                    ))
                
                # 3. Clone schedules and update handoff ID references
                schedules = scheduler_manager.list_schedules(conn=conn)
                for s in schedules:
                    if s.branch_id == origin:
                        new_s = s.model_copy()
                        new_s.schedule_id = str(uuid.uuid4())
                        new_s.branch_id = branch_id
                        # Update references in ordered_handoff_ids
                        new_s.ordered_handoff_ids = [handoff_id_map.get(hid, hid) for hid in s.ordered_handoff_ids]
                        scheduler_manager._save(new_s, conn=conn)
                        
                conn.commit()
                
        logger.info(f"BRANCH CREATED: {branch_id} ({name}) from {origin}")
        self.simulate_branch(branch_id) # Initial simulation
        return self.get_branch(branch_id)

    def get_branches(self) -> List[RoadmapBranch]:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM roadmap_branches WHERE branch_state != 'DISCARDED'").fetchall()
                return [RoadmapBranch.from_row(row) for row in rows]

    def get_branch(self, branch_id: str) -> Optional[RoadmapBranch]:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT * FROM roadmap_branches WHERE branch_id = ?", (branch_id,)).fetchone()
                if row:
                    return RoadmapBranch.from_row(row)
        return None

    def delete_branch(self, branch_id: str):
        if branch_id == "main": return
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("UPDATE roadmap_branches SET branch_state = 'DISCARDED' WHERE branch_id = ?", (branch_id,))
                conn.execute("DELETE FROM mission_handoffs WHERE branch_id = ?", (branch_id,))
                conn.commit()
        
        from backend.core.ai_host.observability.governance_autopsy_engine import autopsy_engine
        autopsy_engine.generate_autopsy(branch_id, "DISCARDED")
        logger.info(f"BRANCH DISCARDED: {branch_id}")

    def simulate_branch(self, branch_id: str):
        """
        OMNIWEB — BLOQUE: SIMULATION / COMPARISON BRIDGE.
        Connects branch with Strategic Simulator and Multi-Persona Simulator.
        """
        from backend.core.ai_host.memory.strategic_sim import strategic_simulator
        from backend.core.ai_host.memory.persona_simulator import persona_simulator
        
        with set_chip_context("core"):
            scenarios = strategic_simulator.generate_scenarios(branch_id=branch_id)
            if not scenarios: return

            # 1. Macro Strategic Analysis
            main_scenarios = strategic_simulator.generate_scenarios(branch_id="main")
            main_friction = sum(m.score for m in main_scenarios[0].projected_friction) if main_scenarios else 0.5
            branch_friction = sum(m.score for m in scenarios[0].projected_friction)
            divergence = abs(branch_friction - main_friction)
            
            # 2. Multi-Persona Governance Audit
            persona_report = persona_simulator.simulate_branch_reaction(branch_id)
            verdict = persona_report.governance_verdict
            
            # 3. Dynamic Readiness Calculation
            # Base readiness from technical friction
            base_readiness = 1.0 if branch_friction <= main_friction else 0.5
            
            # Governance modifiers
            const_status = "PASSED"
            if branch_friction > 1.2 or (verdict and verdict.state == "BLOCKED_BY_PERSONA_TENSION"):
                const_status = "VIOLATED"
                base_readiness = 0.0
            elif verdict and verdict.state == "NEEDS_COMPENSATION":
                base_readiness = min(base_readiness, 0.4)
            elif verdict and verdict.state == "ESCALATE_TO_CREATOR_CORE":
                base_readiness = min(base_readiness, 0.2)
                
            summary = {
                "friction": branch_friction,
                "main_friction": main_friction,
                "improvement": main_friction - branch_friction,
                "confidence": scenarios[0].confidence,
                "recommendations": scenarios[0].recommendations,
                "persona_consensus": persona_report.global_consenus
            }

            with db_manager.get_connection() as conn:
                conn.execute("""
                    UPDATE roadmap_branches SET 
                        divergence_score = ?, 
                        simulation_summary = ?, 
                        merge_readiness = ?, 
                        constitutional_status = ?,
                        persona_verdict = ?,
                        branch_state = 'SIMULATED',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE branch_id = ?
                """, (
                    divergence, 
                    json.dumps(summary), 
                    base_readiness, 
                    const_status, 
                    verdict.model_dump_json() if verdict else None,
                    branch_id
                ))
                
                # 4. Save audit for traceability
                if verdict:
                    self._save_persona_audit(conn, branch_id, verdict)
                    
                conn.commit()
        
        logger.info(f"BRANCH SIMULATED: {branch_id}. Divergence: {divergence:.2f}, Verdict: {verdict.state if verdict else 'NONE'}")

    def _save_persona_audit(self, conn, branch_id: str, verdict: Any):
        audit_id = f"audit_{str(uuid.uuid4())[:8]}"
        conn.execute("""
            INSERT INTO persona_merge_audits (
                audit_id, branch_id, state, severity, rationale, 
                blocking_roles, compensations, bias_score
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            audit_id, 
            branch_id, 
            verdict.state, 
            verdict.severity, 
            verdict.rationale,
            json.dumps(verdict.blocking_roles),
            json.dumps(verdict.required_compensations),
            verdict.merge_bias_score
        ))

    def merge_branch(self, branch_id: str, target: str = "main") -> Dict:
        """
        OMNIWEB — BLOQUE: GOVERNED MERGE LOGIC.
        Refines merge decision by integrating Persona Tension results.
        """
        if branch_id == "main": return {"error": "Cannot merge main into main"}
        
        branch = self.get_branch(branch_id)
        if not branch: return {"error": "Branch not found"}
        
        # 1. Constitution Veto
        if branch.constitutional_status == "VIOLATED":
            return {
                "status": "BLOCKED", 
                "reason": "Constitutional Violation: La rama introduce riesgos tácticos inaceptables.",
                "branch_id": branch_id
            }

        # 2. Persona Tension Veto / Obstacles
        verdict_data = branch.persona_verdict # Should be JSON or None
        if isinstance(verdict_data, str):
            try:
                verdict_data = json.loads(verdict_data)
            except: pass

        if verdict_data:
            state = verdict_data.get("state")
            if state == "BLOCKED_BY_PERSONA_TENSION":
                return {
                    "status": "BLOCKED",
                    "reason": f"Persona Veto: {verdict_data.get('rationale')}",
                    "blocking_roles": verdict_data.get("blocking_roles", []),
                    "branch_id": branch_id
                }
            elif state == "ESCALATE_TO_CREATOR_CORE":
                return {
                    "status": "BLOCKED",
                    "reason": f"Necesita arbitraje manual: {verdict_data.get('rationale')}",
                    "branch_id": branch_id
                }
            elif state == "NEEDS_COMPENSATION":
                # Check if compensation missions were added? 
                # (For now we just block until readiness is higher or it's forced)
                return {
                    "status": "BLOCKED",
                    "reason": f"Requiere compensaciones: {verdict_data.get('rationale')}. Recomendado: {', '.join(verdict_data.get('required_compensations', []))}",
                    "branch_id": branch_id
                }
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Clean current target missions and schedules
                conn.execute("DELETE FROM mission_handoffs WHERE branch_id = ?", (target,))
                conn.execute("DELETE FROM mission_schedules WHERE branch_id = ?", (target,))
                
                # 2. Copy branch missions to target and keep a mapping
                missions = handoff_manager.get_all(branch_id=branch_id, conn=conn)
                handoff_id_map = {}
                for m in missions:
                    old_id = m.handoff_id
                    new_id = str(uuid.uuid4())
                    handoff_id_map[old_id] = new_id
                    
                    conn.execute("""
                        INSERT INTO mission_handoffs (
                            handoff_id, briefing_title, objective, surface_affected, 
                            constraints, risk_level, execution_style, readiness_state, 
                            source_type, gate_data, foreclosure, priority, origin_persona, 
                            supporting_personas, branch_id, ancestry_id
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        new_id, m.briefing_title, m.objective,
                        json.dumps(m.surface_affected), json.dumps(m.constraints),
                        m.risk_level, m.execution_style, m.readiness_state,
                        m.source_type, json.dumps(m.gate_data) if m.gate_data else None,
                        json.dumps(m.foreclosure.model_dump()),
                        m.priority, m.origin_persona, json.dumps(m.supporting_personas),
                        target, m.ancestry_id or old_id
                    ))
                
                # 3. Copy branch schedules to target
                schedules = scheduler_manager.list_schedules(conn=conn)
                for s in schedules:
                    if s.branch_id == branch_id:
                        new_s = s.model_copy()
                        new_s.schedule_id = str(uuid.uuid4())
                        new_s.branch_id = target
                        new_s.ordered_handoff_ids = [handoff_id_map.get(hid, hid) for hid in s.ordered_handoff_ids]
                        scheduler_manager._save(new_s, conn=conn)
                
                # 3. Mark branch as MERGED
                conn.execute("UPDATE roadmap_branches SET branch_state = 'MERGED' WHERE branch_id = ?", (branch_id,))
                conn.commit()
        
        from backend.core.ai_host.observability.governance_autopsy_engine import autopsy_engine
        autopsy_engine.generate_autopsy(branch_id, "MERGED")
        logger.info(f"BRANCH MERGED: {branch_id} -> {target}")
        return {
            "status": "merged", 
            "branch_id": branch_id, 
            "target": target
        }

    def compare_with_main(self, branch_id: str) -> SnapshotDiff:
        """
        OMNIWEB — BLOQUE: SNAPSHOT DIFF ENGINE.
        Detects additions, removals and tactical drifts between main and branch.
        """
        if branch_id == "main":
            return SnapshotDiff(source_branch="main", target_branch="main", summary="No changes in main.")

        branch = self.get_branch(branch_id)
        if not branch: return None
        
        main_missions = handoff_manager.get_all(branch_id="main")
        branch_missions = handoff_manager.get_all(branch_id=branch_id)
        
        main_map = {m.ancestry_id or m.handoff_id: m for m in main_missions}
        branch_map = {m.ancestry_id: m for m in branch_missions if m.ancestry_id}
        branch_added = [m for m in branch_missions if not m.ancestry_id or m.ancestry_id not in main_map]
        
        diff_items = []
        
        # 1. Detect REMOVED
        for aid, m in main_map.items():
            if aid not in branch_map:
                diff_items.append(DiffItem(
                    ancestry_id=aid, type="REMOVED", title=m.briefing_title,
                    delta_details=["Misión descartada en esta rama táctica."]
                ))
        
        # 2. Detect ADDED
        for m in branch_added:
            diff_items.append(DiffItem(
                ancestry_id=m.handoff_id, type="ADDED", title=m.briefing_title,
                delta_details=["Nueva misión experimental añadida."]
            ))
            
        # 3. Detect MODIFIED
        for aid, m_branch in branch_map.items():
            if aid in main_map:
                m_main = main_map[aid]
                deltas = []
                if m_branch.priority != m_main.priority:
                    deltas.append(f"Prioridad {m_main.priority} -> {m_branch.priority}")
                if m_branch.readiness_state != m_main.readiness_state:
                    deltas.append(f"Estado {m_main.readiness_state} -> {m_branch.readiness_state}")
                if m_branch.risk_level != m_main.risk_level:
                    deltas.append(f"Riesgo {m_main.risk_level} -> {m_branch.risk_level}")
                if m_branch.objective != m_main.objective:
                    deltas.append("Objetivo técnico modificado.")
                    
                if deltas:
                    diff_items.append(DiffItem(
                        ancestry_id=aid, type="MODIFIED", title=m_branch.briefing_title,
                        delta_details=deltas
                    ))

        # 4. Strategic Deltas
        main_summary = self.get_branch("main").simulation_summary or {}
        branch_summary = branch.simulation_summary or {}
        
        friction_delta = branch_summary.get("friction", 0.5) - main_summary.get("friction", 0.5)
        
        risk_delta = 0.0
        if any(i.type == "ADDED" and "high" in i.delta_details for i in diff_items): risk_delta = 0.2
        
        const_delta = "NEUTRAL"
        if friction_delta < -0.1: const_delta = "IMPROVED"
        elif friction_delta > 0.1 or branch.constitutional_status == "VIOLATED": const_delta = "DEGRADED"

        # 5. Compensation Audits
        audits = []
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM compensation_effectiveness_audits 
                    WHERE branch_id = ? ORDER BY created_at DESC LIMIT 5
                """, (branch_id,)).fetchall()
                audits = [dict(r) for r in rows]

        diff = SnapshotDiff(
            source_branch="main",
            target_branch=branch_id,
            items=diff_items,
            friction_delta=friction_delta,
            risk_delta=risk_delta,
            constitutional_delta=const_delta,
            persona_verdict=json.loads(branch.persona_verdict) if branch.persona_verdict else None,
            compensation_audits=audits,
            summary=f"Detectados {len(diff_items)} cambios tácticos. {branch.constitutional_status} status."
        )
        return diff

    def get_strategic_dashboard(self) -> StrategicDashboard:
        """
        OMNIWEB — BLOQUE: STRATEGIC AGGREGATION ENGINE.
        Consolidates all active branches into a comparative strategic view.
        """
        branches = self.get_branches()
        summaries = []
        
        for branch in branches:
            # Aggregate status signals
            verdict = json.loads(branch.persona_verdict) if branch.persona_verdict else {}
            v_state = verdict.get("state", "PENDING")
            
            # Compensation check
            audits = []
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM compensation_effectiveness_audits WHERE branch_id = ?", (branch.branch_id,)).fetchall()
                audits = [dict(r) for r in rows]
            
            comp_sum = f"{len([a for a in audits if a['effectiveness_state'] == 'EFFECTIVE'])} efectivos / {len(audits)} total"
            blockers = len(verdict.get("blocking_roles", []))
            
            # Recommendation Logic
            rec = "ITERATE"
            rat = "Rama activa en desarrollo táctico."
            status = "PENDING"
            
            if v_state == "APPROVED":
                rec = "PRIORITIZE_MERGE"
                status = "MERGE_READY"
                rat = "Gobernanza aprobada y alineación fuerte."
            elif v_state == "APPROVED_WITH_WARNING":
                rec = "PRIORITIZE_MERGE"
                status = "MERGE_READY_WITH_WARNING"
                rat = "Aprobado con advertencias menores. Riesgo aceptable."
            elif v_state == "NEEDS_COMPENSATION":
                rec = "COMPENSATE"
                status = "NEEDS_COMPENSATION"
                rat = "Requiere misiones de saneamiento táctico."
            elif v_state == "BLOCKED_BY_PERSONA_TENSION" or branch.constitutional_status == "VIOLATED":
                rec = "ESCALATE"
                status = "BLOCKED"
                rat = "Bloque de gobernanza crítico. Requiere intervención estratégica."
            
            if branch.divergence_score > 0.8 and branch.merge_readiness < 0.3:
                rec = "DISCARD"
                status = "DISCARD_CANDIDATE"
                rat = "Alta divergencia con baja readiness. Considerar descarte."

            # OMNIWEB: DRIFT DETECTION INTEGRATION
            drift = self.detect_governance_drift(branch.branch_id)
            
            summaries.append(BranchStrategicSummary(
                branch_id=branch.branch_id,
                name=branch.name,
                status=status,
                readiness=branch.merge_readiness or 0.0,
                friction=float(branch.simulation_summary.get("friction", 0.5)) if branch.simulation_summary else 0.5,
                divergence=branch.divergence_score,
                constitutional_status=branch.constitutional_status,
                persona_verdict_state=v_state,
                compensation_effect_summary=comp_sum,
                unresolved_blockers_count=blockers,
                recommendation=rec,
                rationale=rat,
                drift_alerts=[d.model_dump() for d in drift],
                last_updated=branch.updated_at
            ))

        # Overall Advisor Advice
        ready_count = len([s for s in summaries if s.status.startswith("MERGE_READY")])
        focus_advice = "No hay ramas listas para merge inmediato."
        if ready_count > 0:
            focus_advice = f"Existen {ready_count} ramas candidatas para merge estratégico. Priorice mayor readiness."
        elif len(summaries) > 3:
            focus_advice = "Alta proliferación de ramas tácticas. Sugerido podar ramas de alta fricción."

        return StrategicDashboard(
            active_branches=summaries,
            focus_recommendation=focus_advice
        )

    def get_branch_dossier(self, branch_id: str) -> BranchDossier:
        """
        OMNIWEB — BLOQUE: ESCALATION DOSSIER ENGINE.
        Aggregates all signals for a high-level arbitration decision.
        """
        branch = self.get_branch(branch_id)
        diff = self.compare_with_main(branch_id)
        
        # 1. Fetch Compensation History
        audits = []
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM compensation_effectiveness_audits WHERE branch_id = ?", (branch_id,)).fetchall()
            audits = [dict(r) for r in rows]
            
        # 2. Extract Persona Friction
        verdict = json.loads(branch.persona_verdict) if branch.persona_verdict else {}
        p_details = verdict.get("persona_details", {})
        friction_map = {role: data.get("friction", 0.5) for role, data in p_details.items()}
        
        # 3. Decision Advice
        adv = "La rama muestra una tensión no resuelta por compensaciones automáticas. Se requiere arbitraje constitucional."
        
        return BranchDossier(
            branch=branch,
            diff=diff,
            compensation_audits=audits,
            persona_friction_map=friction_map,
            recommendation=adv
        )

    def get_exceptions_report(self) -> ExceptionsReport:
        """
        OMNIWEB — BLOQUE: CONSTITUTIONAL EXCEPTIONS REPORT WITH TRIAGE.
        Rebuilds the history with impact classification and noise detection.
        """
        active = []
        resolved = []
        total_debt = 0.0
        
        with db_manager.get_connection() as conn:
            rows = conn.execute("""
                SELECT a.*, b.name as branch_name 
                FROM branch_arbitrations a
                JOIN roadmap_branches b ON a.branch_id = b.branch_id
                ORDER BY a.created_at DESC
            """).fetchall()
            
            for row in rows:
                data = dict(row)
                ex = ConstitutionalException(
                    exception_id=data["arbitration_id"],
                    branch_id=data["branch_id"],
                    branch_name=data["branch_name"],
                    decision=data["decision"],
                    rationale=data["rationale"],
                    conditions=json.loads(data["conditions"]) if data.get("conditions") else [],
                    compliance_state=data["compliance_state"],
                    debt_level=data["debt_level"],
                    created_at=data["created_at"],
                    resolved_at=data["resolved_at"]
                )
                
                ex.triage = self._triage_exception(ex)
                
                if ex.compliance_state in ["PENDING", "PLANNING"]:
                    active.append(ex)
                    total_debt += ex.debt_level
                else:
                    # Includes ARCHIVED, FULFILLED, etc.
                    resolved.append(ex)
                    
        report = ExceptionsReport(
            active_exceptions=active,
            resolved_exceptions=resolved,
            total_debt_score=total_debt
        )
        
        # 2. Extract Memory Patterns
        report.memory_clusters = self.get_governance_patterns(report)
        
        # 3. Generate Strategic Advisories (PHASE 20)
        report.advisories = self.generate_governance_advisories(report.memory_clusters)

        return report

    def _triage_exception(self, ex: ConstitutionalException) -> TriageRecord:
        """
        OMNIWEB — BLOQUE: TRIAGE ENGINE.
        Calculates impact and classification for a single exception.
        """
        # 1. Base Score from decision and debt level
        impact = ex.debt_level
        if ex.decision == "APPROVE_ANYWAY": impact += 2.0
        
        # 2. Factor in persistence
        age_days = (datetime.now() - ex.created_at).days
        persistence = max(1, age_days)
        if persistence > 7: impact += 1.5 
        
        # 3. Final Classification
        if impact >= 6.0: cl = "CRITICAL_DEBT"
        elif impact >= 3.0: cl = "MEDIUM_PRIORITY"
        elif impact >= 1.0: cl = "LOW_IMPACT"
        else: cl = "SIGNAL_NOISE"
        
        rat = f"Impacto {impact:.1f}. Persistencia: {persistence}d. Origen: {ex.decision}."
        if cl == "SIGNAL_NOISE": rat = "Señal técnica menor o bajo impacto sistémico."
        
        return TriageRecord(
            source_id=ex.exception_id,
            classification=cl,
            impact_score=impact,
            persistence=persistence,
            rationale=rat
        )

    def resolve_exception(self, arbitration_id: str, state: str = "FULFILLED") -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: EXCEPTION RESOLUTION.
        Marks a constitutional override as fulfilled or saneado.
        """
        now = datetime.now()
        with db_manager.get_connection() as conn:
            conn.execute("""
                UPDATE branch_arbitrations 
                SET compliance_state = ?, resolved_at = ?, debt_level = 0.0
                WHERE arbitration_id = ?
            """, (state, now, arbitration_id))
            conn.commit()
            
        return {"status": "success", "arbitration_id": arbitration_id, "state": state}

    def generate_recovery_proposals(self, exception_id: str) -> List[RecoveryProposal]:
        """
        OMNIWEB — BLOQUE: DEBT REMEDIATION ENGINE.
        Turns unfulfilled conditions into actionable mission previews.
        """
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM branch_arbitrations WHERE arbitration_id = ?", (exception_id,)).fetchone()
            if not row: return []
            
            ex = dict(row)
            conditions = json.loads(ex["conditions"])
            
        proposals = []
        for cond in conditions:
            # Heuristic conversion: detect keywords
            p_type = "HARDENING_RECOVERY"
            domain = "system_core"
            risk = "LOW"
            
            if "CSS" in cond.upper() or "VISUAL" in cond.upper():
                p_type = "DESIGN_ALIGNMENT_RECOVERY"
                domain = "frontend"
            elif "AUTH" in cond.upper() or "SECURITY" in cond.upper():
                p_type = "GOVERNANCE_RECOVERY"
                domain = "backend_auth"
                risk = "MEDIUM"
                
            proposals.append(RecoveryProposal(
                exception_id=exception_id,
                debt_type="CONSTITUTIONAL_TENSION",
                proposed_mission_type=p_type,
                suggested_objective=f"Sanar deuda constitucional: {cond}",
                suggested_constraints=[f"Referenciar excepción {exception_id}", "No romper flujos existentes"],
                suggested_risk=risk,
                target_domain=domain,
                rationale=f"Esta propuesta ataca directamente la condición '{cond}' impuesta durante el arbitraje de la rama anterior."
            ))
            
        return proposals

    def apply_recovery_proposal(self, proposal: RecoveryProposal) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: RECOVERY INJECT FLOW.
        Registers the remediation mission in the backlog.
        """
        hid = str(uuid.uuid4())
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO mission_handoffs (
                        handoff_id, briefing_title, objective, surface_affected, 
                        constraints, risk_level, readiness_state, source_type, 
                        priority, origin_persona
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hid, f"SANEAMIENTO: {proposal.proposed_mission_type}", proposal.suggested_objective,
                    json.dumps([proposal.target_domain]), json.dumps(proposal.suggested_constraints),
                    proposal.suggested_risk, "READY", "system_governance", 1, "CREATOR_CORE"
                ))
                
                # Mark exception as PLANNING
                conn.execute("UPDATE branch_arbitrations SET compliance_state = 'PLANNING' WHERE arbitration_id = ?", (proposal.exception_id,))
                conn.commit()
                
        return {"status": "success", "mission_id": hid, "state": "PLANNING"}

    def detect_governance_drift(self, branch_id: str) -> List[DriftAlert]:
        """
        OMNIWEB — BLOQUE: DRIFT DETECTION ENGINE.
        Detects if a branch relapses into active constitutional debt.
        """
        branch = self.get_branch(branch_id)
        if not branch.persona_verdict: return []
        
        verdict = json.loads(branch.persona_verdict)
        high_friction_domains = [role for role, data in verdict.get("persona_details", {}).items() if data.get("friction", 0) > 0.6]
        
        # Pull active exceptions
        report = self.get_exceptions_report()
        active = report.active_exceptions
        
        alerts = []
        for ex in active:
            # Simple heuristic: domain overlap or rule overlap
            # 1. Domain relapse
            for role in high_friction_domains:
                # Mock domain to role mapping logic: DESIGNER->frontend, etc.
                if (role == "DESIGNER" and "CSS" in str(ex.conditions).upper()) or \
                   (role == "ARCHITECT" and "AUTH" in str(ex.conditions).upper()):
                    
                    alerts.append(DriftAlert(
                        source_branch_id=branch_id,
                        linked_exception_id=ex.exception_id,
                        drift_type="DOMAIN_RELAPSE",
                        severity="CRITICAL",
                        affected_domain=role,
                        rationale=f"Esta rama está recreando tensión en {role}, la cual ya tiene una excepción activa ({ex.exception_id}). Riesgo de degradación circular.",
                        suggested_action="Reutilizar plan de recovery existente o escalar a Creator Core."
                    ))
                    
            # 2. Rule relapse (heuristic)
            if branch.constitutional_status == "WARNING" and ex.decision == "APPROVE_ANYWAY":
                 alerts.append(DriftAlert(
                        source_branch_id=branch_id,
                        linked_exception_id=ex.exception_id,
                        drift_type="EXCEPTION_REACTIVATION",
                        severity="WARNING",
                        affected_domain="constitution",
                        rationale="Apertura de nueva desviación constitucional mientras una previa sigue sin sanar.",
                        suggested_action="Cerrar la deuda previa antes de avanzar esta rama."
                    ))
                 
        return alerts

        return alerts

    def project_constitutional_health(self, target_id: str, type: str = "exception") -> List[ConstitutionalForecast]:
        """
        OMNIWEB — BLOQUE: CONSTITUTIONAL HEALTH ORACLE.
        Projects future debt and fragility impacts.
        """
        # Base context
        report = self.get_exceptions_report()
        base_debt = report.total_debt_score
        
        forecasts = []
        
        # Scenario 1: DO NOTHING (Siltation)
        debt_future = base_debt * 1.5 # 50% accumulation over time
        fragility = 0.4
        conf = 0.8
        
        forecasts.append(ConstitutionalForecast(
            scenario="DO_NOTHING",
            debt_score=debt_future,
            domain_fragility=fragility,
            governance_load=0.6,
            confidence=conf,
            rationale="La deuda activa tiende a sedimentar, aumentando la fricción en merges futuros y degradando la agilidad del roadmap.",
            recommendation="SANAR_PRONTO"
        ))
        
        # Scenario 2: SANAR_AHORA
        forecasts.append(ConstitutionalForecast(
            scenario="SANAR_AHORA",
            debt_score=max(0.0, base_debt - 2.0),
            domain_fragility=0.1,
            governance_load=0.2,
            confidence=0.9,
            rationale="El saneamiento inmediato desbloquea dominios y reduce la presión de arbitraje en el corto plazo.",
            recommendation="VALOR_ESTRATÉGICO"
        ))
        
        # Scenario 3: ACEPTAR_DERIVA (if target is a branch)
        if type == "branch":
            drift = self.detect_governance_drift(target_id)
            if drift:
                forecasts.append(ConstitutionalForecast(
                    scenario="ACEPTAR_DERIVA",
                    debt_score=base_debt + 3.0,
                    domain_fragility=0.8,
                    governance_load=0.9,
                    confidence=0.7,
                    rationale="Aceptar esta recaída creará una degradación circular que puede obligar a un refactor masivo de infraestructura en el futuro.",
                    recommendation="BLOQUEAR_O_POSTPONER"
                ))

        return forecasts

        return forecasts

    def generate_healing_packages(self) -> List[HealingPackage]:
        """
        OMNIWEB — BLOQUE: SELF-HEALING GROUPING ENGINE.
        Groups minor signals into actionable low-risk batches.
        """
        report = self.get_exceptions_report()
        # Only LOW_IMPACT or SIGNAL_NOISE
        noise = [ex for ex in report.active_exceptions if ex.triage.classification in ["LOW_IMPACT", "SIGNAL_NOISE"]]
        
        if not noise: return []
        
        # 1. Group by "domain" (heuristic based on conditions/rationale)
        domains = {}
        for ex in noise:
            d = "general_tuning"
            if "CSS" in str(ex.conditions).upper() or "VISUAL" in str(ex.conditions).upper():
                d = "ui_cleanup"
            elif "LOGS" in str(ex.conditions).upper() or "DEBUG" in str(ex.conditions).upper():
                d = "observability"
            
            if d not in domains: domains[d] = []
            domains[d].append(ex)
            
        packages = []
        for d_name, signals in domains.items():
            s_ids = [s.exception_id for s in signals]
            
            # Simple 1-to-1 action for now: Cleanup the domain
            action = HealingAction(
                objective=f"Limpieza técnica y saneamiento de ruidos en {d_name}",
                target_domain=d_name,
                rationale=f"Este lote agrupa {len(signals)} señales menores para optimizar la gobernanza del dominio sin saturar el backlog.",
                involved_signal_ids=s_ids
            )
            
            p_name = d_name.upper()
            if "_CLEANUP" not in p_name: p_name += "_CLEANUP"
            p_name += "_BATCH"
            
            packages.append(HealingPackage(
                name=p_name,
                signals=s_ids,
                proposed_actions=[action],
                total_impact_reduction=sum([s.debt_level for s in signals]),
                rationale=f"Agrupamiento prudente de señales repetitivas en {d_name}."
            ))
            
        return packages

    def apply_healing_actions(self, action_ids: List[str], package: HealingPackage) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: GOVERNED HEALING INJECTION.
        Converts selected actions into real mmissions.
        """
        injected_count = 0
        for action in package.proposed_actions:
            if action.action_id in action_ids:
                # Reuse handoff injection logic
                hid = str(uuid.uuid4())
                with set_chip_context("core"):
                    with db_manager.get_connection() as conn:
                        conn.execute("""
                            INSERT INTO mission_handoffs (
                                handoff_id, briefing_title, objective, surface_affected, 
                                constraints, risk_level, readiness_state, source_type, 
                                priority, origin_persona
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            hid, f"HEALING: {package.name}", action.objective,
                            json.dumps([action.target_domain]), json.dumps(["Saneamiento de ruido técnico"]),
                            "LOW", "READY", "system_governance", 0, "HEALING_AGENT"
                        ))
                        
                        # Mark signals as PLANNING
                        for sid in action.involved_signal_ids:
                            conn.execute("UPDATE branch_arbitrations SET compliance_state = 'PLANNING' WHERE arbitration_id = ?", (sid,))
                        conn.commit()
                injected_count += 1
                
        return {"status": "success", "injected_actions": injected_count}

    def get_pruning_candidates(self) -> List[PruningCandidate]:
        """
        OMNIWEB — BLOQUE: PRUNING ENGINE.
        Detects stable minor signals that can leave the active view.
        """
        report = self.get_exceptions_report()
        # Only active LOW_IMPACT or SIGNAL_NOISE
        noise = [ex for ex in report.active_exceptions if ex.triage.classification in ["LOW_IMPACT", "SIGNAL_NOISE"]]
        
        if not noise: return []
        
        candidates = []
        for ex in noise:
            # Heuristic 1: Age (Persistence > 5 days without drift)
            age_days = (datetime.now() - ex.created_at).days
            
            # Heuristic 2: Drift history
            # In a real system, we'd check drift_alerts table; here we check if a signal was in PLANNING (healed)
            is_healed = (ex.compliance_state == "PLANNING")
            
            # Heuristic 3: Stability Score
            # (Simple: 0.5 base + 0.1 per day of age - 0.5 if critical)
            stability = min(1.0, 0.4 + (age_days * 0.05))
            if is_healed: stability += 0.3
            
            # Heuristic 4: Recurrence Gating (PHASE 19)
            risk = self.analyze_recurrence(ex.exception_id)
            
            # To be a candidate: stability > 0.7 AND archive_permission
            if stability >= 0.7:
                can_archive = risk.archive_permission
                c_type = "STABLE"
                if is_healed: c_type = "HEALED"
                if not can_archive: c_type = "RECURRENT_GATED"

                candidates.append(PruningCandidate(
                    signal_id=ex.exception_id,
                    branch_name=ex.branch_name,
                    candidate_type=c_type,
                    stability_score=float(stability),
                    structural_risk_score=risk.structural_risk_score,
                    archive_permission=can_archive,
                    drift_clearance=True, 
                    archive_reason=risk.rationale if not can_archive else 
                                   (f"Señal estabilizada durante {age_days} días sin drift detectado. " + 
                                   ("Saneamiento en progreso." if is_healed else "Bajo impacto recurrente.")),
                    created_at=ex.created_at
                ))
                
        return candidates

    def archive_signals(self, signal_ids: List[str]) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: GOVERNED ARCHIVAL.
        Moves signals to ARCHIVED state (Historical view).
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                for sid in signal_ids:
                    # Mark as ARCHIVED. In report, this moves to resolved_exceptions.
                    conn.execute("""
                        UPDATE branch_arbitrations 
                        SET compliance_state = 'ARCHIVED', resolved_at = ? 
                        WHERE arbitration_id = ?
                    """, (datetime.now(), sid))
                conn.commit()
                
        return {"status": "success", "archived_count": len(signal_ids)}

    def _extract_signature(self, ex: ConstitutionalException) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: SIGNATURE EXTRACTOR.
        Creates a structural fingerprint of an exception.
        """
        raw_text = (ex.rationale + " " + " ".join(ex.conditions)).upper()
        # Heuristic keywords
        keywords = []
        for kw in ["AUTH", "CSS", "UI", "BACKEND", "DATA", "SCHEMA", "SECURITY", "PROMPT", "COGNITIVE", "LOGIC", "THEME"]:
            if kw in raw_text: keywords.append(kw)
            
        # Domains based on text tokens
        domains = []
        text_lower = raw_text.lower()
        if any(token in text_lower for token in ["frontend", "ui", "css", "visual", "layout", "theme"]): 
            domains.append("frontend")
        if any(token in text_lower for token in ["backend", "api", "database", "auth", "logic", "security"]): 
            domains.append("backend")
        
        return {
            "keywords": set(keywords),
            "domains": set(domains),
            "impact": ex.triage.impact_score
        }

    def compute_similarity(self, sig1: Dict[str, Any], sig2: Dict[str, Any]) -> float:
        """
        OMNIWEB — BLOQUE: STRUCTURAL SIMILARITY ENGINE.
        Computes the overlap between two signatures.
        """
        score = 0.0
        # Keyword overlap (Weighted)
        kw_intersect = sig1["keywords"].intersection(sig2["keywords"])
        if kw_intersect: 
            score += len(kw_intersect) * 0.25
            
        # Domain overlap (Strong signal)
        dom_intersect = sig1["domains"].intersection(sig2["domains"])
        if dom_intersect:
            score += len(dom_intersect) * 0.5
            
        return min(1.0, score)

    def get_governance_patterns(self, report: ExceptionsReport) -> List[GovernancePattern]:
        """
        OMNIWEB — BLOQUE: GOVERNANCE MEMORY INDEX.
        Aggregates individual signals into transversal debt clusters.
        """
        all_ex = report.active_exceptions + report.resolved_exceptions
        if not all_ex: return []
        
        signatures = {ex.exception_id: self._extract_signature(ex) for ex in all_ex}
        clusters = []
        processed_ids = set()
        
        for ex in all_ex:
            if ex.exception_id in processed_ids: continue
            
            sig1 = signatures[ex.exception_id]
            family = [ex.exception_id]
            processed_ids.add(ex.exception_id)
            
            for other_ex in all_ex:
                if other_ex.exception_id in processed_ids: continue
                
                sig2 = signatures[other_ex.exception_id]
                similarity = self.compute_similarity(sig1, sig2)
                
                if similarity >= 0.5: # Pattern Match Strong/Possible
                    family.append(other_ex.exception_id)
                    processed_ids.add(other_ex.exception_id)
            
            if len(family) > 1:
                # We found a cluster (Debt Family)
                involved = [e for e in all_ex if e.exception_id in family]
                all_kws = set()
                all_doms = set()
                for e_id in family:
                    all_kws.update(signatures[e_id]["keywords"])
                    all_doms.update(signatures[e_id]["domains"])
                
                risk = "MEDIUM"
                if len(family) >= 3: risk = "HIGH"
                if any(e.triage.classification == "CRITICAL_DEBT" for e in involved): risk = "CRITICAL"
                
                import hashlib
                pid = hashlib.md5("".join(sorted(family)).encode()).hexdigest()[:8]

                clusters.append(GovernancePattern(
                    pattern_id=pid,
                    linked_signal_ids=family,
                    affected_domains=list(all_doms),
                    repeated_keywords=list(all_kws),
                    structural_risk_level=risk,
                    confidence=0.8 if len(family) > 2 else 0.6,
                    rationale=f"Patrón detectado en {len(family)} señales distintas. " + 
                              f"Raíz estructural compartida en dominios: {', '.join(all_doms)}."
                )
)
        return clusters

    def generate_governance_advisories(self, patterns: List[GovernancePattern]) -> List[GovernanceAdvisory]:
        """
        OMNIWEB — BLOQUE: STRATEGIC ADVISORY ENGINE.
        Transforms clusters into actionable structural proposals.
        """
        advisories = []
        for p in patterns:
            # Activation Threshold: 3+ signals OR Critical Risk
            if len(p.linked_signal_ids) >= 3 or p.structural_risk_level == "CRITICAL":
                # Determine Type based on keywords
                a_type = "STRUCTURAL_REFACTOR"
                if "CSS" in p.repeated_keywords or "UI" in p.repeated_keywords:
                    a_type = "SYSTEM_CLEANUP_VISUAL"
                elif "AUTH" in p.repeated_keywords or "SECURITY" in p.repeated_keywords:
                    a_type = "DOMAIN_HARDENING_CORE"
                
                adv = GovernanceAdvisory(
                    advisory_id=f"adv_{p.pattern_id}",
                    source_pattern_id=p.pattern_id,
                    advisory_type=a_type,
                    confidence=p.confidence,
                    structural_risk_level=p.structural_risk_level,
                    affected_domains=p.affected_domains,
                    proposed_objective=f"INTERVENCIÓN ESTRUCTURAL: Sanar patrón {p.pattern_id} (Raíz: {', '.join(p.affected_domains)})",
                    proposed_constraints=["Preservar compatibilidad con Main", "Auditar colaterales en ramas activas"],
                    expected_debt_reduction=len(p.linked_signal_ids) * 0.5,
                    rationale=f"Este clúster ha acumulado {len(p.linked_signal_ids)} señales recurrentes. " + 
                              f"La intervención de raíz puede eliminar permanentemente el drift en {p.affected_domains}."
                )
                
                # Sync with DB
                with set_chip_context("core"):
                    with db_manager.get_connection() as conn:
                        row = conn.execute("SELECT advisory_state, handoff_id FROM governance_advisories WHERE advisory_id = ?", (adv.advisory_id,)).fetchone()
                        if row:
                            adv.advisory_state = row[0]
                            # We don't have a linked mission in the model, but we could add it.
                        else:
                            conn.execute("INSERT INTO governance_advisories (advisory_id, source_pattern_id) VALUES (?, ?)", (adv.advisory_id, adv.source_pattern_id))
                            conn.commit()
                            
                advisories.append(adv)
        return advisories

    def accept_governance_advisory(self, advisory_id: str) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: ADVISORY ACTION FLOW.
        Converts an advisory into a real structural mission.
        """
        report = self.get_exceptions_report()
        adv = next((a for a in report.advisories if a.advisory_id == advisory_id), None)
        if not adv: return {"status": "error", "message": "Advisory no encontrada"}

        # 1. Create a Root Mission
        hid = str(uuid.uuid4())
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO mission_handoffs (
                        handoff_id, briefing_title, objective, surface_affected, 
                        constraints, risk_level, readiness_state, source_type, 
                        priority, origin_persona
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hid, f"ESTRATÉGICA: {adv.proposed_objective}", adv.proposed_objective,
                    json.dumps(adv.affected_domains), json.dumps(adv.proposed_constraints),
                    "HIGH", "READY", "strategic_governance", 1, "OMNIWEB_ADVISOR"
                ))
                # Update Advisory State
                conn.execute("UPDATE governance_advisories SET advisory_state = 'ACCEPTED', handoff_id = ?, updated_at = ? WHERE advisory_id = ?", (hid, datetime.now(), advisory_id))
                conn.commit()

        # 2. Trace
        self._save_audit_trace("SYSTEM", "ADVISORY_ACCEPTED", f"Aceptada intervención para patrón {adv.source_pattern_id}. Misión: {hid}")
        
        return {"status": "success", "mission_id": hid}

    def get_governance_advisory_dashboard(self) -> List[Dict[str, Any]]:
        """
        OMNIWEB — BLOQUE: STRATEGIC ADVISORY DASHBOARD.
        Consolidates states and impact for all advisories.
        """
        report = self.get_exceptions_report()
        patterns_map = {p.pattern_id: p for p in report.memory_clusters}
        
        db_ads = []
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                res = conn.execute("SELECT advisory_id, source_pattern_id, advisory_state, handoff_id, created_at FROM governance_advisories").fetchall()
                for row in res:
                    aid, pid, state, hid, created = row
                    
                    # Calculate Impact (Observed Debt Reduction)
                    # For now: if the cluster still exists, impact is partial.
                    # If signals decreased compared to 'total history', impact is confirmed.
                    curr_p = patterns_map.get(pid)
                    obs_reduction = 0.0
                    recommendation = "PRIORIZAR"
                    
                    if not curr_p and state == "ACCEPTED":
                        obs_reduction = 1.0 # High (Pattern gone)
                        recommendation = "MANTENER EN OBSERVACIÓN"
                        state = "IMPACT_CONFIRMED"
                    elif curr_p and state == "ACCEPTED":
                        obs_reduction = 0.3 # Partial (Cluster persists but might be shrinking)
                        recommendation = "ESCALAR A CREATOR_CORE"

                    if state == "PENDING": recommendation = "EVALUAR RAÍZ"
                    
                    # Fetch from report if available for latest rationale
                    adv_model = next((a for a in report.advisories if a.advisory_id == aid), None)
                    
                    db_ads.append({
                        "advisory_id": aid,
                        "pattern_id": pid,
                        "state": state,
                        "type": adv_model.advisory_type if adv_model else "STRUCTURAL_REFACTOR",
                        "domains": adv_model.affected_domains if adv_model else [],
                        "expected_reduction": adv_model.expected_debt_reduction if adv_model else 0.0,
                        "observed_reduction": obs_reduction,
                        "risk": adv_model.structural_risk_level if adv_model else "MEDIUM",
                        "confidence": adv_model.confidence if adv_model else 0.5,
                        "linked_handoff": hid,
                        "recommendation": recommendation,
                        "created_at": created,
                        "rebase_impacts": self.get_mission_rebase_recommendations(advisory_id=aid)
                    })
        return db_ads

    def get_mission_rebase_recommendations(self, branch_id: str = "main", advisory_id: Optional[str] = None, load_handoffs: bool = True) -> List[Dict[str, Any]]:
        """
        OMNIWEB — BLOQUE: MISSION REBASE ADVISOR ENGINE.
        Detects active or proposed missions supported by a compromised technical base.
        """
        candidates = []
        # 1. Get all active proposals for the branch
        if load_handoffs:
            proposals = handoff_manager.get_all(branch_id=branch_id, load_rebase=False)
            candidates = [
                {"id": m.handoff_id, "title": m.briefing_title, "surfaces": m.surface_affected, "type": "PROPOSAL"}
                for m in proposals if m.readiness_state in ["PENDING", "READY", "BLOCKED"]
            ]
        
        # 2. Add RUNNING missions from mission_manager
        from backend.core.ai_host.memory.mission_manager import mission_manager
        active_missions = mission_manager.get_parallel_running_missions()
        for am in active_missions:
            candidates.append({
                "id": am.mission_id,
                "title": am.active_goal,
                "surfaces": am.related_targets,
                "type": "ACTIVE_MISSION"
            })
        
        if not candidates: return []

        # 3. Get Critical/High Advisories
        report = self.get_exceptions_report()
        relevant_ads = []
        if advisory_id:
            relevant_ads = [a for a in report.advisories if a.advisory_id == advisory_id]
        else:
            relevant_ads = [a for a in report.advisories if a.structural_risk_level in ["HIGH", "CRITICAL"]]

        if not relevant_ads: return []

        # 4. Persistence & Historical Context
        db_recs = {}
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_rebase_recommendations").fetchall()
            for r in rows:
                db_recs[r["affected_handoff_id"]] = dict(r)

        processed_handoffs = set()
        recommendations = []

        # 5. Process LIVE advisories (Priority Detection)
        for adv in relevant_ads:
            for c in candidates:
                # Detection: Domain Overlap
                overlap = set(adv.affected_domains).intersection(set(c["surfaces"]))
                if overlap:
                    risk = adv.structural_risk_level
                    suggested = "REBASE_RECOMMENDED" if risk == "HIGH" else "FREEZE_UNTIL_RECOVERY"
                    
                    # Current state from DB if exists
                    db_state = db_recs.get(c["id"], {})
                    rec_state = db_state.get("recommendation_state", "PENDING")
                    rec_id = db_state.get("recommendation_id")
                    
                    rec = RebaseRecommendation(
                        recommendation_id=rec_id or f"rec_{adv.advisory_id[:8]}_{c['id'][:8]}",
                        source_advisory_id=adv.advisory_id,
                        affected_handoff_id=c["id"],
                        affected_domain=", ".join(overlap),
                        recommendation_state=rec_state,
                        risk_level=risk,
                        suggested_action=suggested,
                        rationale=f"La misión '{c['title']}' toca dominios ({', '.join(overlap)}) comprometidos por la advisory estructural {adv.advisory_id}.",
                        confidence=adv.confidence
                    )
                    
                    # Sync to DB if new
                    if not rec_id:
                        self._save_rebase_recommendation(rec)
                    
                    # UI Payload
                    payload = rec.model_dump()
                    payload["mission_title"] = c["title"]
                    payload["mission_type"] = c["type"]
                    
                    # Check for explicit override
                    with db_manager.get_connection() as conn:
                        ov_row = conn.execute("SELECT debt_state, review_at, degradation_score FROM governance_risk_overrides WHERE recommendation_id = ?", (rec.recommendation_id,)).fetchone()
                        if ov_row:
                            payload["has_active_override"] = True
                            payload["debt_state"] = ov_row["debt_state"]
                            payload["review_at"] = ov_row["review_at"]
                            payload["degradation_score"] = ov_row["degradation_score"]
                        else:
                            payload["has_active_override"] = False
                            payload["debt_state"] = "PENDING"

                    # Timeline
                    payload["pressure_timeline"] = self.get_pressure_timeline(c["id"]).model_dump()
                    
                    recommendations.append(payload)
                    processed_handoffs.add(c["id"])

        # 6. Include Historical OVERRIDDEN items (Accepted Debt that still persists)
        for c in candidates:
            if c["id"] not in processed_handoffs:
                db_state = db_recs.get(c["id"])
                if db_state and db_state.get("recommendation_state") == "OVERRIDDEN":
                    payload = db_state.copy()
                    payload["mission_title"] = c["title"]
                    payload["mission_type"] = c["type"]
                    payload["has_active_override"] = True
                    # Fetch extra details
                    with db_manager.get_connection() as conn:
                        ov_row = conn.execute("SELECT debt_state, review_at, degradation_score FROM governance_risk_overrides WHERE recommendation_id = ?", (db_state["recommendation_id"],)).fetchone()
                        if ov_row:
                            payload["debt_state"] = ov_row["debt_state"]
                            payload["review_at"] = ov_row["review_at"]
                            payload["degradation_score"] = ov_row["degradation_score"]
                    payload["pressure_timeline"] = self.get_pressure_timeline(c["id"]).model_dump()
                    recommendations.append(payload)
        
        return recommendations


    def get_rebase_recommendation_preview(self, rec_id: str) -> Optional[Dict[str, Any]]:
        """
        OMNIWEB — BLOQUE: REBASE RECOMMENDATION PREVIEW ENGINE.
        Generates tactical scenarios (Trade-offs) for a specific recommendation.
        """
        with db_manager.get_connection() as conn:
            row = conn.execute("SELECT * FROM governance_rebase_recommendations WHERE recommendation_id = ?", (rec_id,)).fetchone()
            if not row: return None
            
            # Map columns to dict
            rec_data = dict(row)
            
            # 1. Identify Target Metadata
            target_id = rec_data["affected_handoff_id"]
            target_title = "Unknown Mission"
            target_type = "PROPOSAL"
            
            # Try to find in Proposals first
            p = handoff_manager.get_proposal(target_id)
            if p:
                target_title = p.briefing_title
                target_type = "PROPOSAL"
            else:
                # Try in active missions
                from backend.core.ai_host.memory.mission_manager import mission_manager
                m = mission_manager.get_mission(target_id)
                if m:
                    target_title = m.active_goal
                    target_type = "ACTIVE_MISSION"

            # 2. Build Comparative Scenarios
            risk = rec_data["risk_level"]
            domain = rec_data["affected_domain"]
            
            options = []
            
            # Option A: CONTINUE_AS_IS
            label = "Continuar sin intervención"
            if risk in ["HIGH", "CRITICAL"]:
                label = "ACEPTAR RIESGO ESTRUCTURAL"
                
            options.append(RebasePreviewOption(
                option_id="CONTINUE_AS_IS",
                label=label,
                risk_level=risk,
                tactical_cost="DEUDA TÉCNICA",
                expected_benefit="NONE (Velocidad máxima)",
                rationale=f"Decisión consciente de ignorar la advisory '{rec_data['source_advisory_id']}' y continuar con la base comprometida."
            ))

            # Option B: REVIEW_BEFORE_CONTINUE
            options.append(RebasePreviewOption(
                option_id="REVIEW_BEFORE_CONTINUE",
                label="Revisión Táctica Previa",
                risk_level="MEDIUM",
                tactical_cost="LOW",
                expected_benefit="Detección de puntos de fricción inmediatos",
                rationale="El Creador inspecciona los dominios afectados manualmente. Mitiga riesgos obvios sin forzar un rebase completo.",
                is_recommended=(risk == "MEDIUM")
            ))

            # Option C: REBASE_RECOMMENDED
            options.append(RebasePreviewOption(
                option_id="REBASE_RECOMMENDED",
                label="Sincronizar base (REBASE)",
                risk_level="LOW",
                tactical_cost="MEDIUM",
                expected_benefit="Alineación constitucional y eliminación de deuda técnica",
                rationale="Se adapta la misión a los nuevos patrones estructurales. Garantiza que el código resultante sea 'future-proof'.",
                is_recommended=(risk == "HIGH")
            ))

            # Option D: FREEZE_UNTIL_RECOVERY
            options.append(RebasePreviewOption(
                option_id="FREEZE_UNTIL_RECOVERY",
                label="Congelar Misión (FREEZE)",
                risk_level="NONE",
                tactical_cost="HIGH (Bloqueo de flujo)",
                expected_benefit="Cero riesgo de divergencia",
                rationale="La base técnica está demasiado inestable. Continuar es destructivo. Detener el trabajo hasta que la advisory sea resuelta.",
                is_recommended=(risk == "CRITICAL")
            ))

            preview = RebasePreview(
                recommendation_id=rec_id,
                source_advisory_id=rec_data["source_advisory_id"],
                target_id=target_id,
                target_title=target_title,
                affected_domain=domain,
                current_risk_state=risk,
                options=options,
                final_recommendation=rec_data["suggested_action"],
                confidence=rec_data["confidence"]
            )
            
            # Attach Pressure Timeline
            timeline = self.get_pressure_timeline(target_id)
            res = preview.model_dump()
            res["pressure_timeline"] = timeline.model_dump()
            
            return res


    def get_pressure_timeline(self, target_id: str) -> PressureTimeline:
        """
        OMNIWEB — BLOQUE: PRESSURE RECONSTRUCTION ENGINE.
        Rebuilds the history of governance pressure for a mission/handoff.
        """
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_pressure_events WHERE target_id = ? ORDER BY timestamp ASC", (target_id,)).fetchall()
            
            events = []
            for r in rows:
                events.append(GovernancePressureEvent(
                    event_id=r[0],
                    target_id=r[1],
                    event_type=r[2],
                    source_advisory_id=r[3],
                    risk_level=r[4],
                    creator_decision=r[5],
                    rationale=r[6],
                    timestamp=datetime.fromisoformat(r[7])
                ))
                
            if not events:
                # Return empty/default if no events
                return PressureTimeline(
                    target_id=target_id,
                    events=[],
                    first_detected_at=datetime.now(),
                    duration_hours=0.0,
                    current_status="NOMINAL",
                    trajectory="NO_PRESSURE",
                    summary="No se ha detectado presión de gobernanza sobre este objeto."
                )
            
            # Interpretar Trayectoria
            first = events[0].timestamp
            last = events[-1].timestamp
            duration = (datetime.now() - first).total_seconds() / 3600.0
            
            # Heuristics
            risk_levels = [e.risk_level for e in events]
            decisions = [e.creator_decision for e in events if e.creator_decision]
            
            trajectory = "PERSISTENT_PRESSURE"
            if len(events) == 1:
                trajectory = "TEMPORARY_ALERT"
            elif any(d == "IGNORED" for d in decisions) and risk_levels[-1] in ["HIGH", "CRITICAL"]:
                trajectory = "IGNORED_AND_DEGRADED"
            elif any(d == "ACCEPTED" for d in decisions):
                trajectory = "REVIEWED_AND_STABILIZED"
            elif risk_levels.count("CRITICAL") > 0:
                trajectory = "ESCALATING_PRESSURE"

            summary = f"Presión detectada hace {duration:.1f} horas. Origen: {events[0].source_advisory_id}."
            if trajectory == "IGNORED_AND_DEGRADED":
                summary += " La alerta fue ignorada y el riesgo estructural persiste o ha escalado."

            return PressureTimeline(
                target_id=target_id,
                events=events,
                first_detected_at=first,
                duration_hours=duration,
                current_status=events[-1].risk_level,
                trajectory=trajectory,
                summary=summary
            )


    def _save_rebase_recommendation(self, rec: RebaseRecommendation):
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT OR IGNORE INTO governance_rebase_recommendations (
                        recommendation_id, source_advisory_id, affected_handoff_id, 
                        affected_domain, recommendation_state, risk_level, 
                        suggested_action, rationale, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    rec.recommendation_id, rec.source_advisory_id, rec.affected_handoff_id,
                    rec.affected_domain, rec.recommendation_state, rec.risk_level,
                    rec.suggested_action, rec.rationale, rec.confidence
                ))
                conn.commit()
                
                # Record Initial Detection Event
                self._record_pressure_event(GovernancePressureEvent(
                    target_id=rec.affected_handoff_id,
                    event_type="PRESSURE_DETECTED",
                    source_advisory_id=rec.source_advisory_id,
                    risk_level=rec.risk_level,
                    rationale=rec.rationale
                ))

    def _record_pressure_event(self, event: GovernancePressureEvent, conn: sqlite3.Connection = None):
        """
        OMNIWEB — BLOQUE: PRESSURE TIMELINE RECORDER.
        Persists a single event in the mission pressure history.
        """
        if conn:
            self._execute_pressure_insert(conn, event)
        else:
            with db_manager.get_connection() as conn_new:
                self._execute_pressure_insert(conn_new, event)
                conn_new.commit()

    def _execute_pressure_insert(self, conn: sqlite3.Connection, event: GovernancePressureEvent):
        conn.execute("""
            INSERT INTO governance_pressure_events (
                event_id, target_id, event_type, source_advisory_id, 
                risk_level, creator_decision, rationale, timestamp,
                debt_state, review_due_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            event.event_id, event.target_id, event.event_type, 
            event.source_advisory_id, event.risk_level, 
            event.creator_decision, event.rationale, 
            event.timestamp.isoformat(),
            event.debt_state,
            event.review_due_at.isoformat() if event.review_due_at else None
        ))

    def update_rebase_recommendation(self, recommendation_id: str, state: str) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: REBASE ACTION FLOW.
        Updates the decision for a mission rebase recommendation.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Update Recommendation State
                conn.execute("UPDATE governance_rebase_recommendations SET recommendation_state = ?, updated_at = CURRENT_TIMESTAMP WHERE recommendation_id = ?", (state, recommendation_id))
                
                # 2. Record Decision Event for Timeline
                row_full = conn.execute("SELECT * FROM governance_rebase_recommendations WHERE recommendation_id = ?", (recommendation_id,)).fetchone()
                if row_full:
                    r = dict(row_full)
                    type_map = {
                        "ACCEPTED": "REBASE_ACCEPTED",
                        "IGNORED": "PRESSURE_IGNORED",
                        "REVIEWED": "PRESSURE_REVIEWED",
                        "POSTPONED": "PRESSURE_POSTPONED",
                        "OVERRIDDEN": "PRESSURE_OVERRIDDEN"
                    }
                    event_type = type_map.get(state, "PRESSURE_REVIEWED")
                    
                    self._record_pressure_event(GovernancePressureEvent(
                        target_id=r["affected_handoff_id"],
                        event_type=event_type,
                        source_advisory_id=r["source_advisory_id"],
                        risk_level=r["risk_level"],
                        creator_decision=state,
                        rationale=f"Acción del Creador: {state} (Asesoría: {r['suggested_action']})"
                    ))

                    # 3. Register Action Trace
                    trace_engine.register_trace(r["affected_handoff_id"], state, domain=r.get("affected_domain", "Global"))

                    # 4. Register in Strategic Ledger (PHASE 109)
                    governance_ledger_engine.record_decision(
                        decision_type="STRATEGIC_PIVOT",
                        target_ref_type="MISSION",
                        target_id=r["affected_handoff_id"],
                        actor="CREATOR",
                        action_taken=state,
                        rationale=f"Decisión táctica sobre advisory {r['source_advisory_id']}.",
                        evidence_refs={"recommendation_id": recommendation_id, "source_advisory": r["source_advisory_id"]},
                        severity_context=r["risk_level"]
                    )
                
                conn.commit()
        return {"status": "success", "recommendation_id": recommendation_id, "state": state}

    def apply_risk_override(self, override: RiskOverride) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: RISK OVERRIDE ENGINE.
        Persists a conscious decision by the creator to proceed with structural debt.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Update Recommendation State to OVERRIDDEN
                conn.execute("UPDATE governance_rebase_recommendations SET recommendation_state = ?, updated_at = CURRENT_TIMESTAMP WHERE recommendation_id = ?", ("OVERRIDDEN", override.recommendation_id))
                
                # 2. Record Decision Event for Timeline
                row_full = conn.execute("SELECT * FROM governance_rebase_recommendations WHERE recommendation_id = ?", (override.recommendation_id,)).fetchone()
                r = dict(row_full) if row_full else {}
                
                # Initial Follow-up review scheduled (24h)
                review_due = datetime.now() + timedelta(hours=24)
                if not override.review_at: override.review_at = review_due

                self._record_pressure_event(GovernancePressureEvent(
                    target_id=override.target_id,
                    event_type="PRESSURE_OVERRIDDEN",
                    source_advisory_id=override.source_advisory_id or r.get("source_advisory_id"),
                    risk_level=override.risk_level,
                    creator_decision="OVERRIDDEN",
                    rationale=f"OVERRIDE: {override.rationale[:100]}",
                    review_due_at=review_due
                ), conn=conn)

                # 3. Create Override Record
                conn.execute("""
                    INSERT INTO governance_risk_overrides (
                        override_id, recommendation_id, target_id, override_type, 
                        risk_level, rationale, conditions, expiry_at, created_at,
                        debt_state, review_at, degradation_score, oracle_pressure_delta,
                        affected_domain, source_advisory_id, priority_rank
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    override.override_id, override.recommendation_id, override.target_id,
                    override.override_type, override.risk_level, override.rationale,
                    json.dumps(override.conditions), 
                    override.expiry_at.isoformat() if override.expiry_at else None,
                    datetime.now().isoformat(), "ACTIVE",
                    override.review_at.isoformat() if isinstance(override.review_at, datetime) else override.review_at,
                    0.0, 0.0,
                    override.affected_domain or r.get("affected_domain", "Global"),
                    override.source_advisory_id or r.get("source_advisory_id"),
                    0
                ))
                
                # 4. Register in Strategic Ledger (PHASE 109)
                governance_ledger_engine.record_decision(
                    decision_type="RISK_OVERRIDE",
                    target_ref_type="BRANCH" if override.target_id.startswith('br_') else "MISSION",
                    target_id=override.target_id,
                    actor="CREATOR",
                    action_taken="ACCEPTED_DEBT",
                    rationale=f"OVERRIDE: {override.rationale}",
                    evidence_refs={"recommendation_id": override.recommendation_id, "advisory_id": override.source_advisory_id or r.get("source_advisory_id")},
                    severity_context=override.risk_level
                )

                # 5. Register Action Trace
                trace_engine.register_trace(override.target_id, "ACCEPT_RISK", domain=override.affected_domain or r.get("affected_domain", "Global"))
                
                conn.commit()
                
                # Final notification in trace
                self._save_audit_trace("SYSTEM", "RISK_OVERRIDE_ISSUED", f"Override issued for {override.target_id} with rationale: {override.rationale[:50]}...")
        
        return {"status": "success", "override_id": override.override_id}

    def audit_accepted_debt(self, conn: sqlite3.Connection = None) -> List[RiskOverride]:
        """
        OMNIWEB — BLOQUE: ACCEPTED DEBT FOLLOW-UP ENGINE.
        Audits all risk overrides to detect expiry, degradation or need for review.
        """
        now = datetime.now()
        report = self.get_exceptions_report() # Expensive but necessary for degradation detection
        
        updated_overrides = []
        
        def _process(db_conn):
            rows = db_conn.execute("SELECT * FROM governance_risk_overrides WHERE debt_state != 'CLOSED'").fetchall()
            for row in rows:
                ov = RiskOverride(**dict(row))
                original_state = ov.debt_state
                
                # A. Temporal Checks
                if ov.expiry_at and isinstance(ov.expiry_at, str):
                    ov.expiry_at = datetime.fromisoformat(ov.expiry_at)
                    
                if ov.expiry_at and now > ov.expiry_at:
                    ov.debt_state = "OVERDUE"
                    ov.next_required_action = "RECOVERY_OR_RENEW"
                elif ov.review_at and now > (datetime.fromisoformat(ov.review_at) if isinstance(ov.review_at, str) else ov.review_at) and ov.debt_state == "ACTIVE":
                    ov.debt_state = "REVIEW_DUE"
                    ov.next_required_action = "MANUAL_REVIEW"
                
                # B. Degradation Check (Structural Signals)
                # Find current advisories that overlap with the same domains as the target
                rec_row = db_conn.execute("SELECT affected_domain FROM governance_rebase_recommendations WHERE recommendation_id = ?", (ov.recommendation_id,)).fetchone()
                if rec_row:
                    target_domains = [d.strip() for d in rec_row[0].split(",")]
                    
                    # Search for LIVE advisories in these domains
                    overlapping_ads = [a for a in report.advisories if any(d in a.affected_domains for d in target_domains)]
                    
                    if overlapping_ads:
                        # NEW pressure detected in the same domain!
                        ov.degradation_score = min(1.0, ov.degradation_score + (0.1 * len(overlapping_ads)))
                        if ov.degradation_score >= 0.5:
                            ov.debt_state = "DEGRADED"
                            ov.next_required_action = "STRUCTURAL_REVIEW"
                
                # C. Persistence
                if ov.debt_state != original_state or ov.degradation_score > float(row["degradation_score"]):
                    # Ensure dates are stored as ISO strings
                    rv_at = ov.review_at.isoformat() if isinstance(ov.review_at, datetime) else ov.review_at
                    lr_at = (ov.last_reviewed_at.isoformat() if isinstance(ov.last_reviewed_at, datetime) else ov.last_reviewed_at) if ov.last_reviewed_at else None

                    db_conn.execute("""
                        UPDATE governance_risk_overrides 
                        SET debt_state = ?, degradation_score = ?, next_required_action = ?, last_reviewed_at = ?, review_at = ?
                        WHERE override_id = ?
                    """, (ov.debt_state, ov.degradation_score, ov.next_required_action, lr_at, rv_at, ov.override_id))
                    
                    # Record Event in Timeline if state changed significantly
                    if ov.debt_state in ["OVERDUE", "DEGRADED", "REVIEW_DUE"] and ov.debt_state != original_state:
                         self._record_pressure_event(GovernancePressureEvent(
                            target_id=ov.target_id,
                            event_type="DEBT_DEGRADED" if ov.debt_state == "DEGRADED" else "PRESSURE_ESCALATED",
                            source_advisory_id="LIFECYCLE_ENGINE",
                            risk_level=ov.risk_level,
                            rationale=f"Lifecycle update: Deuda aceptada ahora en estado {ov.debt_state}. Acción: {ov.next_required_action}",
                            debt_state=ov.debt_state
                        ), conn=db_conn)

                updated_overrides.append(ov)
            db_conn.commit()

        if conn:
            _process(conn)
        else:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn_new:
                    _process(conn_new)
                
        return updated_overrides

    def get_risk_overrides(self) -> List[RiskOverride]:
        """
        OMNIWEB — BLOQUE: RISK OVERRIDE RETRIEVAL.
        Returns all non-closed technical debt overrides.
        """
        overrides = []
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM governance_risk_overrides WHERE debt_state != 'CLOSED'").fetchall()
            for row in rows:
                overrides.append(RiskOverride(**dict(row)))
        return overrides

    def get_accepted_debt_dashboard(self) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: GOVERNANCE DEBT COCKPIT.
        Aggregates all active overrides, pressure, and degradation into a single cockpit view.
        """
        overrides = self.audit_accepted_debt()
        
        # 1. Group by domain
        by_domain = {}
        for ov in overrides:
            domain = ov.affected_domain or "System (Global)"
            if domain not in by_domain: by_domain[domain] = []
            by_domain[domain].append(ov)
            
        # 2. Prioritization & Interpretation
        # We define "URGENT INTERVENTION" as OVERDUE + DEGRADED or HIGH RISK + OVERDUE
        critical_alerts = []
        for ov in overrides:
            if ov.debt_state in ["OVERDUE", "DEGRADED"] or (ov.risk_level in ["HIGH", "CRITICAL"] and ov.debt_state == "REVIEW_DUE"):
                critical_alerts.append({
                    "id": ov.override_id,
                    "target": ov.target_id,
                    "affected_domain": ov.affected_domain,
                    "reason": f"Deuda {ov.debt_state} en {ov.affected_domain}. Score Degradación: {ov.degradation_score:.2f}",
                    "level": "CRITICAL" if ov.risk_level == "CRITICAL" or ov.debt_state == "DEGRADED" else "HIGH",
                    "next_step": ov.next_required_action or "RECOVERY_REQUIRED"
                })

        summary = {
            "total_active_debt": len([o for o in overrides if o.debt_state != "CLOSED"]),
            "overdue_count": len([o for o in overrides if o.debt_state == "OVERDUE"]),
            "degraded_count": len([o for o in overrides if o.debt_state == "DEGRADED"]),
            "review_due_count": len([o for o in overrides if o.debt_state == "REVIEW_DUE"]),
            "critical_risk_count": len([o for o in overrides if o.risk_level == "CRITICAL"]),
            "intervention_required": sorted(critical_alerts, key=lambda x: x["level"] == "CRITICAL", reverse=True)
        }

        # 3. Build the Dashboard Payload
        return {
            "summary": summary,
            "domains": [
                {
                    "name": dom,
                    "overrides": [o.model_dump() for o in ovs],
                    "risk_burden": sum([1.0 if o.risk_level == "CRITICAL" else 0.5 for o in ovs]),
                    "status": "CRITICAL" if any(o.debt_state in ["DEGRADED", "OVERDUE"] for o in ovs) else "WARNING" if any(o.debt_state == "REVIEW_DUE" for o in ovs) else "ACTIVE"
                } for dom, ovs in by_domain.items()
            ],
            "generated_at": datetime.now().isoformat()
        }

    def review_risk_override(self, id_or_rec_id: str, decision: str, rationale: str) -> Dict[str, Any]:
        """
        Manually reviews an existing override to renew it or close it.
        Supports both override_id and recommendation_id.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Find the override
                row = conn.execute("SELECT * FROM governance_risk_overrides WHERE override_id = ?", (id_or_rec_id,)).fetchone()
                if not row:
                    row = conn.execute("SELECT * FROM governance_risk_overrides WHERE recommendation_id = ?", (id_or_rec_id,)).fetchone()
                
                if not row: return {"status": "error", "message": f"Override/Recommendation not found: {id_or_rec_id}"}
                
                ov = RiskOverride(**dict(row))
                ov.last_reviewed_at = datetime.now()
                
                if decision == "RENEW":
                    ov.debt_state = "ACTIVE"
                    # Push review date 48h further by default
                    ov.review_at = datetime.now() + timedelta(hours=48)
                    ov.degradation_score = 0.0 # Reset degradation on renew
                    # If it was expired, give it 24h more
                    if ov.expiry_at and datetime.now() > (datetime.fromisoformat(ov.expiry_at) if isinstance(ov.expiry_at, str) else ov.expiry_at):
                         ov.expiry_at = datetime.now() + timedelta(hours=24)
                elif decision == "CLOSE":
                    ov.debt_state = "CLOSED"
                elif decision == "ESCALATE":
                    ov.debt_state = "DEGRADED"
                    ov.next_required_action = "CREATOR_CORE_ARBITRATION"
                
                conn.execute("""
                    UPDATE governance_risk_overrides 
                    SET debt_state = ?, review_at = ?, last_reviewed_at = ?, rationale = rationale || '\n[REVIEW]: ' || ?, degradation_score = ?, expiry_at = ?
                    WHERE override_id = ?
                """, (
                    ov.debt_state, 
                    ov.review_at.isoformat() if isinstance(ov.review_at, datetime) else ov.review_at, 
                    ov.last_reviewed_at.isoformat(), 
                    rationale, 
                    ov.degradation_score,
                    ov.expiry_at.isoformat() if isinstance(ov.expiry_at, datetime) else ov.expiry_at,
                    ov.override_id
                ))
                
                # Record in timeline
                self._record_pressure_event(GovernancePressureEvent(
                    target_id=ov.target_id,
                    event_type="DEBT_REVIEWED",
                    source_advisory_id="MANUAL_REVIEW",
                    risk_level=ov.risk_level,
                    creator_decision=decision,
                    rationale=f"Review manual ({decision}): {rationale}",
                    debt_state=ov.debt_state
                ), conn=conn)
                
                conn.commit()
            
        return {"status": "success", "new_state": ov.debt_state, "override_id": ov.override_id}

    def analyze_recurrence(self, signal_id: str) -> RecurrenceRisk:
        """
        OMNIWEB — BLOQUE: RECURRENCE DETECTION ENGINE.
        Analyzes the forensics timeline to detect patterns of relapse, 
        false stability, or circular recovery.
        """
        replay = self.get_forensics_replay(signal_id)
        
        recovery_count = len([e for e in replay.events if e.event_type == "RECOVERY"])
        archived_once = any(e.event_type == "ARCHIVED" for e in replay.events)
        
        # Heuristics for Recurrence State
        state = "STABLE"
        score = 0.0
        permission = True
        confidence = 0.85
        action = "MONITOR"
        
        if recovery_count >= 2:
            state = "RECURRENT"
            score = 0.6
            permission = False
            action = "RECOVERY"
        
        if archived_once and recovery_count > 0:
            state = "FRAGILE"
            score = 0.4
            confidence = 0.6
            action = "MONITOR"
            
        rationale = f"Se detectaron {recovery_count} misiones de recuperación. "
        
        # Transversal Check: Does this signal belong to a high-risk memory cluster?
        report = self.get_exceptions_report()
        patterns = report.memory_clusters
        cluster = next((p for p in patterns if signal_id in p.linked_signal_ids), None)
        
        if cluster:
            if cluster.structural_risk_level in ["HIGH", "CRITICAL"]:
                state = "RECURRENT"
                permission = False
                score = max(score, 0.7)
                rationale += f"Vinculada a un clúster de deuda transversal ({cluster.pattern_id}). "

        if state == "CRITICAL": rationale += "Patrón de recaída circular que indica deuda estructural profunda."
        elif state == "RECURRENT": rationale += "La señal tiende a persistir tras intentos de saneamiento parcial."
        elif state == "FRAGILE": rationale += "Señal previamente archivada que ha requerido recuperación táctica."
        elif recovery_count == 0 and state == "STABLE": rationale = "Trayectoria nominal con estabilidad comprobada."

        return RecurrenceRisk(
            signal_id=signal_id,
            recurrence_state=state,
            recurrence_count=recovery_count,
            structural_risk_score=score,
            archive_permission=permission,
            confidence=confidence,
            rationale=rationale,
            next_required_action=action
        )

    def get_forensics_replay(self, signal_id: str) -> ForensicsReplay:
        """
        OMNIWEB — BLOQUE: REPLAY ENGINE.
        Reconstructs the timeline of an exception or signal.
        """
        with db_manager.get_connection() as conn:
            # 1. Base arbitration (Creation)
            row = conn.execute("""
                SELECT a.*, b.name as branch_name 
                FROM branch_arbitrations a
                JOIN roadmap_branches b ON a.branch_id = b.branch_id
                WHERE a.arbitration_id = ?
            """, (signal_id,)).fetchone()
            
            if not row: raise ValueError("Signal not found")
            data = dict(row)
            
            events = []
            events.append(ForensicsEvent(
                event_type="CREATED",
                timestamp=datetime.fromisoformat(data["created_at"]) if isinstance(data["created_at"], str) else data["created_at"],
                title=f"Excepción Detectada en '{data['branch_name']}'",
                description=f"Se detectó una desviación constitucional. Rationale: {data['rationale']}",
                debt_impact=data["debt_level"]
            ))
            
            # 2. Search for related remediation missions
            # Search briefing_title or use metadata if available
            missions = conn.execute("""
                SELECT * FROM mission_handoffs 
                WHERE briefing_title LIKE ?
            """, (f"%{signal_id}%",)).fetchall()
            
            for m in missions:
                events.append(ForensicsEvent(
                    event_type="RECOVERY",
                    timestamp=datetime.fromisoformat(m["created_at"]) if isinstance(m["created_at"], str) else m["created_at"],
                    title=f"Misión de Recuperación: {m['briefing_title']}",
                    description=f"Inyectada para sanar la señal. Estado: {m['readiness_state']}",
                    debt_impact=-0.2, # Theoretical relief
                    link_id=m["handoff_id"]
                ))
                
            # 3. Check archival
            if data["compliance_state"] == "ARCHIVED":
                events.append(ForensicsEvent(
                    event_type="ARCHIVED",
                    timestamp=datetime.fromisoformat(data["resolved_at"]) if data["resolved_at"] else datetime.now(),
                    title="Señal Archivada",
                    description="Clasificada como ruido estable. Movida al histórico por el creador.",
                    debt_impact=0.0
                ))
                
            # Sort events by time
            events.sort(key=lambda x: x.timestamp)
            
            # 4. Trajectory Analysis
            trajectory = "STABILIZING"
            current_debt = data["debt_level"]
            recovery_count = len([ev for ev in events if ev.event_type == "RECOVERY"])
            
            if recovery_count > 0:
                trajectory = "RESOLVING"
            if recovery_count >= 3:
                trajectory = "STRUCTURAL_REVIEW"
            elif recovery_count >= 2:
                trajectory = "RECURRENT_DRIFT"
            
            if data["compliance_state"] == "ARCHIVED":
                trajectory = "ARCHIVED"
                
            summary = "La señal ha seguido una trayectoria "
            if trajectory == "ARCHIVED": summary += "de archivado prudente tras un periodo de estabilidad."
            elif trajectory == "STRUCTURAL_REVIEW": summary += "de degradación recurrente que exige una revisión estructural del dominio."
            elif trajectory == "RECURRENT_DRIFT": summary += "de recaídas múltiples que dificultan el saneamiento definitivo."
            elif trajectory == "RESOLVING": summary += "de saneamiento activo mediante misiones de recuperación."
            else: summary += "de observación pasiva con deuda persistente."
            
            # 5. Pattern Context
            report = self.get_exceptions_report()
            cluster = next((p for p in report.memory_clusters if signal_id in p.linked_signal_ids), None)
            if cluster:
                summary += f" Esta señal pertenece al clúster de memoria '{cluster.pattern_id}', compartiendo raíz estructural con {len(cluster.linked_signal_ids)-1} otras deudas."
                if cluster.structural_risk_level == "CRITICAL":
                    trajectory = "STRUCTURAL_REVIEW"

            return ForensicsReplay(
                target_id=signal_id,
                events=events,
                trajectory=trajectory,
                current_debt=current_debt,
                total_recurrence=recovery_count,
                summary=summary
            )

    def apply_arbitration_decision(self, branch_id: str, decision: str, rationale: str, conditions: List[str] = []) -> ArbitrationRecord:
        """
        OMNIWEB — BLOQUE: GOVERNED ARBITRATION OVERRIDE.
        Applies a high-level decision from CREATOR_CORE.
        """
        arb = ArbitrationRecord(
            branch_id=branch_id,
            escalation_reason="STRATEGIC_CONFLICT", # TODO: dynamic
            decision=decision,
            rationale=rationale,
            conditions=conditions
        )
        
        new_state = "ACTIVE"
        is_arbitrated = 1
        
        if decision == "APPROVE_ANYWAY":
            new_state = "READY_FOR_MERGE"
        elif decision == "APPROVE_WITH_CONDITIONS":
            new_state = "READY_FOR_MERGE"
        elif decision == "REJECT_VETO":
            new_state = "DISCARDED"
        elif decision == "POSTPONE":
            new_state = "ACTIVE"
        
        with db_manager.get_connection() as conn:
            # 1. Save Arbitration
            conn.execute("""
                INSERT INTO branch_arbitrations (
                    arbitration_id, branch_id, escalation_reason, 
                    decision, rationale, conditions
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                arb.arbitration_id, arb.branch_id, arb.escalation_reason,
                arb.decision, arb.rationale, json.dumps(arb.conditions)
            ))
            
            # 2. Update Branch State
            conn.execute("""
                UPDATE roadmap_branches 
                SET branch_state = ?, is_arbitrated = ?, arbitration_id = ? 
                WHERE branch_id = ?
            """, (new_state, is_arbitrated, arb.arbitration_id, branch_id))
            
            # 3. If Discarded, mark in roadmap
            if new_state == "DISCARDED":
                conn.execute("UPDATE roadmap_branches SET branch_state = 'DISCARDED' WHERE branch_id = ?", (branch_id,))
                
            conn.commit()
            
        # 4. Trace the decision
        self._save_audit_trace(branch_id, f"ARBITRATED_{decision}", f"Decisión: {decision}. Rationale: {rationale}")
        
        return arb

    def inject_compensation(self, branch_id: str, comp_id: str) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: COMPENSATION INJECT.
        Creates a real mission from a suggested compensation.
        """
        branch = self.get_branch(branch_id)
        if not branch or not branch.persona_verdict:
            return {"status": "error", "message": "No hay veredicto de personas para esta rama."}
        
        verdict = json.loads(branch.persona_verdict)
        missions = verdict.get("suggested_missions", [])
        chosen = next((m for m in missions if m["compensation_id"] == comp_id), None)
        
        if not chosen:
            return {"status": "error", "message": "Propuesta de compensación no encontrada."}
            
        # 0. Capture BEFORE state
        before_state = {
            "state": verdict.get("state"),
            "friction": float(branch.simulation_summary.get("friction", 0.5)) if branch.simulation_summary else 0.5,
            "readiness": float(branch.merge_readiness or 0.0),
            "persona_details": verdict.get("persona_details", {})
        } if branch.persona_verdict else {"state": "UNKNOWN", "friction": 0.5, "readiness": 0.0, "persona_details": {}}

        # 1. Create the Mission
        from backend.core.ai_host.memory.handoff_manager import handoff_manager
        
        mission_payload = {
            "objective": chosen["objective"],
            "surface_affected": [chosen["target_domain"]],
            "risk_level": chosen["suggested_risk"],
            "constraints": chosen["suggested_constraints"],
            "origin_persona": chosen["persona_role"]
        }
        
        # We need to save it specifically for this branch
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Reuse handoff_manager SQL logic but specify branch_id
                hid = str(uuid.uuid4())
                conn.execute("""
                    INSERT INTO mission_handoffs (
                        handoff_id, briefing_title, objective, surface_affected, 
                        constraints, risk_level, readiness_state, source_type, 
                        priority, origin_persona, branch_id
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    hid, f"COMPENSACIÓN: {chosen['type']}", chosen["objective"],
                    json.dumps([chosen["target_domain"]]), json.dumps(chosen["suggested_constraints"]),
                    chosen["suggested_risk"], "READY", "system_governance", 0, chosen["persona_role"], branch_id
                ))
                conn.commit()
        
        # 2. Record Trace
        self._save_audit_trace(branch_id, "COMPENSATION_INJECTED", f"Inyectada misión {chosen['type']} sugerida por {chosen['persona_role']}.")
        
        # 3. RE-AUDIT loop: re-simulate
        self.simulate_branch(branch_id)
        
        # 4. Capture AFTER state and EVALUATE EFFECTIVENESS
        updated_branch = self.get_branch(branch_id)
        updated_verdict = json.loads(updated_branch.persona_verdict) if updated_branch.persona_verdict else {}
        
        after_state = {
            "state": updated_verdict.get("state"),
            "friction": float(updated_branch.simulation_summary.get("friction", 0.5)) if updated_branch.simulation_summary else 0.5,
            "readiness": float(updated_branch.merge_readiness or 0.0),
            "persona_details": updated_verdict.get("persona_details", {})
        }
        
        from backend.core.ai_host.memory.persona_simulator import persona_simulator
        effect_audit = persona_simulator.evaluate_compensation_effectiveness(branch_id, comp_id, before_state, after_state)
        self._save_effectiveness_audit(effect_audit)

        return {
            "status": "success",
            "mission_id": hid,
            "effectiveness": effect_audit.model_dump(),
            "message": f"Compensación '{chosen['type']}' inyectada y auditada: {effect_audit.effectiveness_state}."
        }

    def revert_compensation(self, branch_id: str, mission_id: str) -> Dict[str, Any]:
        """
        OMNIWEB — BLOQUE: LOGICAL REVERT.
        Discards a mission that was injected as a compensation.
        """
        # 1. Discard the mission from the branch
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("DELETE FROM mission_handoffs WHERE handoff_id = ? AND branch_id = ?", (mission_id, branch_id))
                conn.commit()
        
        # 2. Record Trace
        self._save_audit_trace(branch_id, "COMPENSATION_REVERTED", f"Revertida misión compensatoria {mission_id}.")
        
        # 3. RE-AUDIT loop: re-simulate
        self.simulate_branch(branch_id)
        
        return {
            "status": "success",
            "message": "Misión revertida y rama re-auditada."
        }
        
    def _save_effectiveness_audit(self, audit: Any):
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO compensation_effectiveness_audits (
                        audit_id, branch_id, compensation_id, effectiveness_state, 
                        before_state, after_state, friction_delta, readiness_delta, 
                        persona_deltas, recommended_next_action, rationale
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit.audit_id, audit.branch_id, audit.compensation_id, audit.effectiveness_state,
                    audit.before_state, audit.after_state, audit.friction_delta, audit.readiness_delta,
                    json.dumps(audit.persona_deltas), audit.recommended_next_action, audit.rationale
                ))
                conn.commit()

    def _save_audit_trace(self, branch_id: str, action: str, note: str):
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO persona_merge_audits (audit_id, branch_id, state, rationale)
                    VALUES (?, ?, ?, ?)
                """, (str(uuid.uuid4()), branch_id, action, note))
                conn.commit()

    def perform_pre_mission_check(self, target_id: str, target_type: str = "PROPOSAL") -> PreMissionCheck:
        """
        OMNIWEB — BLOQUE: PRE-MISSION GOVERNANCE CHECK ENGINE.
        Consolidates all governance signals before starting a mission.
        """
        signals = []
        status = "SAFE_TO_START"
        
        # 1. Fetch Basic Info
        proposal = None
        branch_id = "main"
        affected_domains = []
        
        with set_chip_context("core"):
            if target_type == "PROPOSAL":
                proposal = handoff_manager.get_proposal(target_id)
                if proposal:
                    branch_id = proposal.branch_id
                    affected_domains = proposal.surface_affected
            
            # 2. Constitutional Audit (Core Rules)
            from backend.core.ai_host.memory.constitutional_auditor import constitutional_auditor
            if proposal:
                const_audit = constitutional_auditor.audit_mission(proposal)
                if const_audit.status != "COMPLIANT":
                    signals.append(PreMissionCheckSignal(
                        type="CONSTITUTION",
                        severity="CRITICAL" if const_audit.status == "BLOCKED" else "WARNING",
                        source_id="CONSTITUTIONAL_AUDITOR",
                        message=const_audit.summary
                    ))
                    if const_audit.status == "BLOCKED": status = "REVIEW_REQUIRED"
            
            # 3. Debt & Rebase Audit
            recs = self.get_mission_rebase_recommendations(branch_id=branch_id, load_handoffs=True)
            target_recs = [r for r in recs if r["affected_handoff_id"] == target_id]
            
            overdue_debt = 0
            degraded_debt = 0
            pending_rebase = False
            critical_overlap = 0
            
            for r in target_recs:
                # A. Advisory Overlap
                if r["risk_level"] == "CRITICAL":
                    critical_overlap += 1
                    signals.append(PreMissionCheckSignal(
                        type="ADVISORY",
                        severity="CRITICAL",
                        source_id=r["source_advisory_id"],
                        message=f"Crítica: Esta misión toca dominios ({r['affected_domain']}) con falla estructural grave activa."
                    ))
                    status = "REBASE_RECOMMENDED"
                
                # B. Pending Rebase (Not reviewed yet)
                if r["recommendation_state"] == "PENDING":
                    pending_rebase = True
                    signals.append(PreMissionCheckSignal(
                        type="REBASE",
                        severity="WARNING",
                        source_id=r["recommendation_id"],
                        message="Rebase pendiente identificado para este dominio."
                    ))
                    if status == "SAFE_TO_START": status = "START_WITH_WARNING"
                
                # C. Accepted Debt State
                # We need to reach into the override details if it exists
                with db_manager.get_connection() as conn:
                    ov = conn.execute("SELECT debt_state, degradation_score FROM governance_risk_overrides WHERE recommendation_id = ?", (r["recommendation_id"],)).fetchone()
                    if ov:
                        if ov["debt_state"] == "OVERDUE":
                            overdue_debt += 1
                            signals.append(PreMissionCheckSignal(
                                type="DEBT",
                                severity="CRITICAL",
                                source_id=r["recommendation_id"],
                                message="Deuda aceptada VENCIDA en este dominio."
                            ))
                            status = "REVIEW_REQUIRED"
                        elif ov["debt_state"] == "DEGRADED":
                            degraded_debt += 1
                            signals.append(PreMissionCheckSignal(
                                type="DEBT",
                                severity="WARNING",
                                source_id=r["recommendation_id"],
                                message=f"Deuda degradándose (Score: {ov['degradation_score']:.1f})."
                            ))
                            if status in ["SAFE_TO_START", "START_WITH_WARNING"]: status = "REVIEW_REQUIRED"

            # 4. Pressure Timeline
            timeline = self.get_pressure_timeline(target_id)
            if timeline.trajectory == "ESCALATING_PRESSURE":
                signals.append(PreMissionCheckSignal(
                    type="PRESSURE",
                    severity="CRITICAL",
                    source_id="PRESSURE_TIMELINE",
                    message="Presión escalada persistente detectada sobre este objetivo."
                ))
                status = "ESCALATE_TO_CREATOR_CORE"
            
            # 5. Domain Fragility (Oracle)
            forecasts = self.project_constitutional_health(target_id, type="handoff")
            do_nothing = next((f for f in forecasts if f.scenario == "DO_NOTHING"), None)
            if do_nothing and do_nothing.domain_fragility > 0.6:
                signals.append(PreMissionCheckSignal(
                    type="FRAGILITY",
                    severity="WARNING",
                    source_id="ORACLE",
                    message=f"Fragilidad de dominio alta: {do_nothing.domain_fragility:.1f}."
                ))
                if status == "SAFE_TO_START": status = "START_WITH_WARNING"

            # 6. Final Logic Override: Critical overlap with high fragility
            if critical_overlap > 0 and (do_nothing and do_nothing.domain_fragility > 0.7):
                status = "FREEZE_UNTIL_RECOVERY"
            
            # Assembly
            check = PreMissionCheck(
                target_id=target_id,
                target_type=target_type,
                branch_id=branch_id,
                status=status,
                signals=signals,
                active_overdue_debt=overdue_debt,
                degraded_debt=degraded_debt,
                critical_advisory_overlap=critical_overlap,
                rebase_pending=pending_rebase,
                rationale=f"Check de gobernanza completado. Estado: {status}. Señales detectadas: {len(signals)}.",
                suggested_action=self._get_suggestion_for_precheck(status)
            )
            
            # Persistence
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO pre_mission_governance_checks (
                        check_id, target_id, target_type, branch_id, 
                        resulting_status, rationale, signals_json, confidence
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    check.check_id, check.target_id, check.target_type, check.branch_id,
                    check.status, check.rationale, json.dumps([s.model_dump() for s in signals]), check.confidence
                ))
                conn.commit()
            
            return check

    def _get_suggestion_for_precheck(self, status: str) -> str:
        smap = {
            "SAFE_TO_START": "Proceder con normalidad.",
            "START_WITH_WARNING": "Proceder, pero monitorear drift.",
            "REVIEW_REQUIRED": "Revisar deuda o presión antes de seguir.",
            "REBASE_RECOMMENDED": "Se recomienda Sincronizar (Rebase) la base técnica primero.",
            "FREEZE_UNTIL_RECOVERY": "Base técnica inestable. Detener misión hasta recuperación de salud.",
            "ESCALATE_TO_CREATOR_CORE": "Requiere arbitraje estratégico del Creador Core."
        }
        return smap.get(status, "Consultar Gobernanza.")

    def register_precheck_decision(self, check_id: str, decision: str) -> bool:
        """Records the creator's decision following a pre-mission check."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("UPDATE pre_mission_governance_checks SET creator_decision = ? WHERE check_id = ?", (decision, check_id))
                conn.commit()
                
                # If they decide to CONTINUE anyway, record it in the timeline
                row = conn.execute("SELECT target_id, resulting_status FROM pre_mission_governance_checks WHERE check_id = ?", (check_id,)).fetchone()
                if row and decision == "CONTINUE":
                    self._record_pressure_event(GovernancePressureEvent(
                        target_id=row["target_id"],
                        event_type="PRESSURE_OVERRIDDEN",
                        source_advisory_id="PRECHECK_HOOK",
                        risk_level="HIGH" if row["resulting_status"] in ["REVIEW_REQUIRED", "REBASE_RECOMMENDED"] else "MEDIUM",
                        creator_decision="CONTINUE_UNDER_WARNING",
                        rationale=f"Creator bypassed pre-mission hook status: {row['resulting_status']}"
                    ))
                    
                    # 2. Register Action Trace
                    # Try to fetch domain if it's a mission
                    domain = "Global"
                    prop = handoff_manager.get_proposal(row["target_id"])
                    if prop and prop.surface_affected:
                        domain = prop.surface_affected[0]
                    
                    trace_engine.register_trace(row["target_id"], decision, domain=domain)
                    
                return True

branch_manager = BranchManager()

