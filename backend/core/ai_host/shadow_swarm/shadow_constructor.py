import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime
from .shadow_auditor import ShadowState, ShadowType

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

class ShadowConstructorProposal(BaseModel):
    microtask: str
    target_file: str
    target_block: str
    proposed_change: str
    diff_preview: str # Pseudo-diff or actual diff
    risk_assessment: str
    affected_layers: List[str]
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
    context: Dict[str, Any] = {} # Metadata and operation results

    def assign(self, microtask: str, layer: str, file: str = None):
        self.assigned_microtask = microtask
        self.target_layer = layer
        self.target_file = file
        self.state = ConstructorState.ASSIGNED
        logger.info(f"[SHADOW-CONST-{self.shadow_id}] Assigned to: {microtask} on {layer} ({file})")

    async def draft_proposal(self) -> ShadowConstructorProposal:
        self.state = ConstructorState.DRAFTING
        logger.info(f"[SHADOW-CONST-{self.shadow_id}] Drafting proposal for: {self.assigned_microtask}")
        
        # Real logic would analyze the file and generate a diff
        # Simulation for this phase:
        
        proposal = ShadowConstructorProposal(
            microtask=self.assigned_microtask,
            target_file=self.target_file or "core/module.py",
            target_block="L24-L32",
            proposed_change="Optimizar validación de entrada para evitar redundancia.",
            diff_preview="- if data and 'key' in data:\n+ if data.get('key'):",
            risk_assessment="Bajo impacto. Cambio local sin efectos colaterales detectados.",
            affected_layers=[self.target_layer],
            requires_human_approval=True
        )
        
        self.proposal = proposal
        self.state = ConstructorState.PROPOSED
        return proposal

class ShadowConstructorManager:
    """
    Manages the lifecycle and state of Shadow Constructors.
    """
    def __init__(self):
        self.active_constructors: Dict[str, ShadowConstructor] = {}

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
        return constructor

    def get_constructors_for_mission(self, mission_id: str) -> List[ShadowConstructor]:
        return [s for s in self.active_constructors.values() if s.mission_id == mission_id]

shadow_constructor_manager = ShadowConstructorManager()
