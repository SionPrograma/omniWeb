import logging
import json
import uuid
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .shadow_auditor import ShadowState, ShadowType, ShadowAuditorReport, RiskCategory

logger = logging.getLogger(__name__)

class ConstructorState(Enum):
    IDLE = "idle"
    ASSIGNED = "assigned"
    DRAFTING = "drafting"
    PROPOSED = "proposed"
    # Gate Transitions
    AWAITING_AUDIT = "awaiting_audit"
    AWAITING_HUMAN = "awaiting_human_approval"
    BLOCKED_BY_RISK = "blocked_by_risk"
    ESCALATED = "escalated"
    READY_FOR_APPLY = "ready_for_apply"
    REJECTED = "rejected"
    # Apply Transitions
    APPLYING = "applying"
    APPLIED_PENDING_VERIFY = "applied_pending_verification"
    VERIFIED_SUCCESS = "verified_success"
    VERIFIED_FAILED = "failed_verification"
    ROLLBACK_NEEDED = "rollback_needed"

class DecisionTrace(BaseModel):
    main_hypothesis: str
    alternatives_considered: List[str]
    risks_detected: List[str]
    chosen_path: str
    discarded_paths: List[str]
    evidence_used: str
    final_outcome: str

class ShadowConstructorProposal(BaseModel):
    microtask: str
    target_file: str
    target_block: str
    proposed_change: str
    diff_preview: str # Pseudo-diff or actual diff
    risk_assessment: str
    affected_layers: List[str]
    cognitive_trace: Optional[DecisionTrace] = None
    no_touch_zones_respected: bool = True
    requires_human_approval: bool = True
    status: str = "PENDING_REVIEW"
    timestamp: datetime = datetime.now()

class ShadowConstructor(BaseModel):
    shadow_id: str
    type: ShadowType = ShadowType.CONSTRUCTOR
    mission_id: str
    assigned_microtask: str
    target_layer: str
    target_file: Optional[str] = None
    state: ConstructorState = ConstructorState.IDLE
    proposal: Optional[ShadowConstructorProposal] = None
    auditor_note: Optional[str] = None # Cross-validation note from ShadowAuditor
    was_redrafted: bool = False
    context: Dict[str, Any] = {} # Metadata and operation results

    def assign(self, microtask: str, layer: str, file: str = None):
        self.assigned_microtask = microtask
        self.target_layer = layer
        self.target_file = file
        self.state = ConstructorState.ASSIGNED
        logger.info(f"[SHADOW-CONST-{self.shadow_id}] Assigned to: {microtask} on {layer} ({file})")
    async def draft_proposal(self, audit_report: Optional['ShadowAuditorReport'] = None) -> ShadowConstructorProposal:
        self.state = ConstructorState.DRAFTING
        logger.info(f"[SHADOW-CONST-{self.shadow_id}] Drafting risk-aware proposal for: {self.assigned_microtask}")
        
        # Risk-Aware Logic
        strategy = "Optimizar validación de entrada para evitar redundancia."
        diff = "- if data and 'key' in data:\n+ if data.get('key'):"
        risk_assessment = "Bajo impacto. Cambio local sin efectos colaterales detectados."
        requires_approval = True
        
        audit_findings = "No context audit available."
        is_high_risk = False
        
        if audit_report:
            audit_findings = f"Audit detected: {', '.join(audit_report.findings)}"
            if any(r.name in ["SHARED_LAYER_RISK", "HIGH_BLAST_RADIUS"] for r in audit_report.granular_risks):
                is_high_risk = True
                strategy = "[CONSERVADOR] Ajuste mínimo de validación para evitar impacto en capa compartida."
                risk_assessment = f"RIESGO DETECTADO: {audit_report.risk_level}. Afecta a {', '.join(audit_report.affected_components)}"
                requires_approval = True # Hard enforce

        proposal = ShadowConstructorProposal(
            microtask=self.assigned_microtask,
            target_file=self.target_file or "core/module.py",
            target_block="L24-L32",
            proposed_change=strategy,
            diff_preview=diff,
            risk_assessment=risk_assessment,
            affected_layers=[self.target_layer],
            cognitive_trace=DecisionTrace(
                main_hypothesis=f"La optimización es viable {'pero requiere cautela' if is_high_risk else 'y segura'}.",
                alternatives_considered=["Refactor total", "Mantener actual", "Patch quirúrgico"],
                risks_detected=[r.value for r in (audit_report.granular_risks if audit_report else [])],
                chosen_path=strategy,
                discarded_paths=["Refactor total (Alto riesgo/Blast radius)" if is_high_risk else "Mantener actual (No-op)"],
                evidence_used=audit_findings,
                final_outcome="Draft generado bajo criterio preventivo de auditoría."
            ),
            requires_human_approval=requires_approval
        )
        
        self.proposal = proposal
        self.state = ConstructorState.PROPOSED
        
        if shadow_constructor_manager:
            shadow_constructor_manager.save_constructor(self)
            
        return proposal

    async def redraft_proposal(self, feedback: str):
        """
        Refines the proposal based on conflict or audit feedback before elevation.
        """
        if not self.proposal: return
        
        logger.info(f"[SHADOW-CONST-{self.shadow_id}] AUTO-CORRECTING proposal: {feedback}")
        
        # Save historical trace of the draft before correcting
        initial_draft = self.proposal.model_dump()
        
        # Apply Correction logic (Simulation)
        self.proposal.proposed_change = f"[AUTO-CORREGIDO] {self.proposal.proposed_change}"
        self.proposal.risk_assessment = f"CORRECCIÓN: {feedback}. Versión más conservaora generada para evitar conflictos."
        self.proposal.cognitive_trace.evidence_used += f" | Loop de autocorrección disparado por: {feedback}"
        self.proposal.cognitive_trace.final_outcome = "Redraft completado: Propuesta mitigada."
        
        # Store initial draft in metadata or extra field if needed for UI
        self.proposal.requires_human_approval = True
        self.was_redrafted = True
        
        if shadow_constructor_manager:
            shadow_constructor_manager.save_constructor(self)

class ShadowConstructorManager:
    """
    Manages the lifecycle and state of Shadow Constructors.
    """
    def __init__(self):
        self.active_constructors: Dict[str, ShadowConstructor] = {}
        self._rehydrate()

    def _rehydrate(self):
        """Loads proposals from DB on startup."""
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    cursor = conn.execute("SELECT * FROM swarm_proposals")
                    rows = cursor.fetchall()
                    for row in rows:
                        proposal_obj = None
                        if row["proposal_json"]:
                            # Pydantic validation
                            proposal_obj = ShadowConstructorProposal.model_validate_json(row["proposal_json"])
                        
                        constructor = ShadowConstructor(
                            shadow_id=row["shadow_id"],
                            mission_id=row["mission_id"],
                            assigned_microtask=row["microtask"],
                            target_layer=row["target_layer"],
                            target_file=row["target_file"],
                            state=ConstructorState(row["state"]),
                            proposal=proposal_obj,
                            auditor_note=row["auditor_note"],
                            context=json.loads(row["context_json"] or "{}")
                        )
                        self.active_constructors[constructor.shadow_id] = constructor
            logger.info(f"[SWARM_MANAGER] Rehydrated {len(self.active_constructors)} constructors.")
        except Exception as e:
            logger.error(f"[SWARM_MANAGER] Rehydration failed: {e}")

    def save_constructor(self, constructor: ShadowConstructor):
        """Persists a shadow constructor state to DB."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                query = """
                INSERT OR REPLACE INTO swarm_proposals (
                    shadow_id, mission_id, microtask, target_layer, 
                    target_file, state, proposal_json, auditor_note, 
                    context_json, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                proposal_json = constructor.proposal.model_dump_json() if constructor.proposal else None
                conn.execute(query, (
                    constructor.shadow_id,
                    constructor.mission_id,
                    constructor.assigned_microtask,
                    constructor.target_layer,
                    constructor.target_file,
                    constructor.state.value,
                    proposal_json,
                    constructor.auditor_note,
                    json.dumps(constructor.context),
                    datetime.now()
                ))
                conn.commit()

    def spawn_constructor(self, mission_id: str, microtask: str, layer: str, file: str = None) -> ShadowConstructor:
        shadow_id = f"shadow_const_{len(self.active_constructors) + 1:03d}"
        constructor = ShadowConstructor(
            shadow_id=shadow_id,
            mission_id=mission_id,
            assigned_microtask=microtask,
            target_layer=layer,
            target_file=file,
            state=ConstructorState.ASSIGNED
        )
        self.active_constructors[shadow_id] = constructor
        self.save_constructor(constructor)
        return constructor

    def get_constructors_for_mission(self, mission_id: str) -> List[ShadowConstructor]:
        return [s for s in self.active_constructors.values() if s.mission_id == mission_id]

shadow_constructor_manager = ShadowConstructorManager()
