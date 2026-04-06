import logging
import hashlib
import json
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.core.ai_host.memory.persona_sync import persona_sync
from backend.core.ai_host.memory.handoff_manager import handoff_manager

logger = logging.getLogger(__name__)

class CompensationEffectAudit(BaseModel):
    audit_id: str = Field(default_factory=lambda: "audit_" + hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])
    branch_id: str
    compensation_id: str
    effectiveness_state: str # EFFECTIVE, PARTIAL, INSUFFICIENT, REDUNDANT, BACKFIRED
    
    before_state: str
    after_state: str
    
    friction_delta: float # (after - before) - lower is better
    readiness_delta: float # (after - before) - higher is better
    persona_deltas: Dict[str, float] = {} # role -> delta
    
    unresolved_tensions: List[str] = []
    recommended_next_action: str # MAINTAIN, EXPAND, COMPLEMENT, REVERT, ESCALATE
    rationale: str

class CompensationProposal(BaseModel):
    compensation_id: str = Field(default_factory=lambda: "comp_" + hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])
    type: str # HARDENING, TESTING, SYNC, GOVERNANCE, CLEANUP, DESIGN
    persona_role: str
    target_domain: str # core, ui, tests, shared, etc.
    objective: str
    rationale: str
    expected_impact: str # Lower friction, improved consensus, stability.
    suggested_risk: str = "low"
    suggested_constraints: List[str] = []
    already_exists: bool = False
    existing_mission_id: Optional[str] = None
    
class PersonaResponse(BaseModel):
    persona_id: str
    role: str
    support_score: float # 0.0 to 1.0
    friction_score: float # 0.0 to 1.0
    governance_concern: float = 0.0
    domain_bias: str = "NEUTRAL" # FAVORED, NEGLECTED, NEUTRAL
    rationale: str
    recommendation: Optional[str] = None
    structured_proposal: Optional[CompensationProposal] = None

class MergeGovernanceVerdict(BaseModel):
    state: str # APPROVED, APPROVED_WITH_WARNING, NEEDS_COMPENSATION, BLOCKED_BY_PERSONA_TENSION, ESCALATE_TO_CREATOR_CORE
    severity: str = "nominal" # nominal, warning, high, critical
    rationale: str
    blocking_roles: List[str] = []
    required_compensations: List[str] = []
    suggested_missions: List[CompensationProposal] = []
    persona_details: Dict[str, Dict[str, float]] = {} # role -> {support, friction}
    merge_bias_score: float = 0.0 # 0.0 to 1.0 (how much it favors one role over others)

class ConsensusReport(BaseModel):
    simulation_id: str = Field(default_factory=lambda: str(hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8]))
    target_branch_id: str
    responses: List[PersonaResponse]
    global_consenus: str # STRONG_ALIGNMENT, MIXED, CONSTITUTIONALLY_TENSE, HIGH_FRICTION
    governance_verdict: Optional[MergeGovernanceVerdict] = None
    architectural_debt_warning: bool = False
    design_drift_warning: bool = False
    summary: str
    generated_at: datetime = Field(default_factory=datetime.now)

class MultiPersonaSimulator:
    """
    OMNIWEB — BLOQUE: MULTI-PERSONA SIMULATION ENGINE.
    Projects how different creator roles react to a branch strategy.
    """
    
    def simulate_branch_reaction(self, branch_id: str) -> ConsensusReport:
        from backend.core.ai_host.memory.branch_manager import branch_manager
        
        branch = branch_manager.get_branch(branch_id)
        if not branch: return None
        
        missions = handoff_manager.get_all(branch_id=branch_id)
        responses = []
        
        # 1. ARCHITECT Projection
        responses.append(self._project_architect(missions))
        
        # 2. DESIGNER Projection
        responses.append(self._project_designer(missions))
        
        # 3. TESTER Projection
        responses.append(self._project_tester(missions))
        
        # 4. AUDITOR Projection
        responses.append(self._project_auditor(missions, branch))
        
        # 5. Evaluate Merge Governance
        verdict = self.evaluate_merge_governance(responses, branch)
        
        # 6. Duplicate Detection for Compensations
        self._check_for_duplicates(branch_id, verdict)
        
        # consensus logic
        avg_support = sum(r.support_score for r in responses) / len(responses)
        avg_friction = sum(r.friction_score for r in responses) / len(responses)
        
        consenus = "MIXED"
        if avg_support > 0.8 and avg_friction < 0.2: consenus = "STRONG_ALIGNMENT"
        elif any(r.governance_concern > 0.7 for r in responses): consenus = "CONSTITUTIONALLY_TENSE"
        elif avg_friction > 0.6: consenus = "HIGH_FRICTION"
        
        summary = f"Simulación de Consenso: {consenus}. Soporte promedio del {int(avg_support*100)}%."

        return ConsensusReport(
            target_branch_id=branch_id,
            responses=responses,
            global_consenus=consenus,
            governance_verdict=verdict,
            architectural_debt_warning=any(r.role == "ARCHITECT" and r.friction_score > 0.5 for r in responses),
            design_drift_warning=any(r.role == "DESIGNER" and r.friction_score > 0.5 for r in responses),
            summary=summary
        )


    def _check_for_duplicates(self, branch_id: str, verdict: MergeGovernanceVerdict):
        """
        Scans existing missions in the branch to find matches for suggested compensations.
        """
        existing_missions = handoff_manager.get_all(branch_id=branch_id)
        
        for prop in verdict.suggested_missions:
            # Simple heuristic: title starts with "COMPENSACIÓN: {type}" or same domain + intent
            match = next((m for m in existing_missions if 
                (prop.type.upper() in m.briefing_title.upper() and prop.target_domain in m.surface_affected) or
                (prop.objective.lower() in m.objective.lower())
            ), None)
            
            if match:
                prop.already_exists = True
                prop.existing_mission_id = match.handoff_id

    def evaluate_compensation_effectiveness(self, branch_id: str, comp_id: str, before: Dict, after: Dict) -> CompensationEffectAudit:
        """
        Calculates the delta between before/after and determines effectiveness.
        """
        # Lower friction is better
        f_delta = after.get("friction", 0.5) - before.get("friction", 0.5)
        # Higher readiness is better
        r_delta = after.get("readiness", 0.0) - before.get("readiness", 0.0)
        
        # Per-persona deltas
        b_responses = before.get("responses", []) # List of PersonaResponse dicts
        a_responses = after.get("responses", [])
        
        p_deltas = {}
        b_map = {r["role"]: r["friction_score"] for r in b_responses}
        a_map = {r["role"]: r["friction_score"] for r in a_responses}
        
        for role, a_fric in a_map.items():
            b_fric = b_map.get(role, 0.5)
            p_deltas[role] = a_fric - b_fric

        # State Priority
        prio = {"APPROVED": 0, "APPROVED_WITH_WARNING": 1, "NEEDS_COMPENSATION": 2, "ESCALATE_TO_CREATOR_CORE": 3, "BLOCKED_BY_PERSONA_TENSION": 4}
        b_prio = prio.get(before.get("state"), 4)
        a_prio = prio.get(after.get("state"), 4)
        
        effectiveness = "INSUFFICIENT"
        next_action = "EXPAND"
        
        if a_prio < b_prio:
            effectiveness = "EFFECTIVE" if a_prio <= 1 else "PARTIAL"
            next_action = "MAINTAIN" if a_prio == 0 else "COMPLEMENT"
        elif f_delta < -0.1:
            effectiveness = "PARTIAL"
            next_action = "COMPLEMENT"
        elif f_delta > 0.1:
            effectiveness = "BACKFIRED"
            next_action = "REVERT"
        elif any(d > 0.2 for d in p_deltas.values()):
            effectiveness = "PARTIAL" # One improved, one worsened
            next_action = "COMPLEMENT"
            rationale += " Se detecta un trade-off: la mejora en un área incrementó la fricción en otra."
        elif abs(f_delta) < 0.05 and abs(r_delta) < 0.05:
            effectiveness = "REDUNDANT"
            next_action = "ESCALATE"

        rationale = f"Cambio de fricción: {f_delta:+.2f}, readiness: {r_delta:+.2f}."
        if effectiveness == "EFFECTIVE":
            rationale += " La compensación resolvió el factor crítico de bloqueo."
        elif effectiveness == "PARTIAL":
            rationale += " Se observa alivio táctico pero la tensión persiste en otros roles."
        else:
            rationale += " La intervención no fue suficiente para mover el Merge Gate."

        return CompensationEffectAudit(
            branch_id=branch_id,
            compensation_id=comp_id,
            effectiveness_state=effectiveness,
            before_state=before.get("state", "UNKNOWN"),
            after_state=after.get("state", "UNKNOWN"),
            friction_delta=f_delta,
            readiness_delta=r_delta,
            persona_deltas=p_deltas,
            recommended_next_action=next_action,
            rationale=rationale
        )

    def evaluate_merge_governance(self, responses: List[PersonaResponse], branch: Any) -> MergeGovernanceVerdict:
        """
        OMNIWEB — BLOQUE: PERSONA TENSION GATE ENGINE.
        Turns individual persona reactions into a final merge governance decision.
        """
        max_friction = max(r.friction_score for r in responses)
        avg_support = sum(r.support_score for r in responses) / len(responses)
        blocking_roles = [r.role for r in responses if r.friction_score > 0.6]
        
        # Calculate Bias: max support - min support
        supports = [r.support_score for r in responses]
        bias_score = max(supports) - min(supports)
        
        compensations = [r.recommendation for r in responses if r.recommendation]
        suggested_missions = [r.structured_proposal for r in responses if r.structured_proposal]
        persona_details = {r.role: {"support": r.support_score, "friction": r.friction_score} for r in responses}
        
        # Determine State
        state = "APPROVED"
        severity = "nominal"
        rationale = "Consenso inter-persona positivo. Equilibrio de roles detectado."
        
        # 1. Hard Veto from Auditor (Constitution)
        if any(r.role == "AUDITOR" and r.governance_concern > 0.8 for r in responses):
            state = "BLOCKED_BY_PERSONA_TENSION"
            severity = "critical"
            rationale = "BLOQUEO: El Auditor detecta riesgos constitucionales graves en la propuesta."
        
        # 2. High Friction (Multiple Blockers)
        elif len(blocking_roles) >= 2:
            state = "ESCALATE_TO_CREATOR_CORE"
            severity = "critical"
            rationale = f"ESCALACIÓN: Tensión crítica multi-rol ({', '.join(blocking_roles)}). Se requiere arbitraje de CREATOR_CORE."
            
        # 3. High Friction (Single Blocker)
        elif len(blocking_roles) == 1:
            state = "NEEDS_COMPENSATION"
            severity = "high"
            rationale = f"CORRECCIÓN: {blocking_roles[0]} detecta fricción alta. Se requieren misiones compensatorias."
 
        # 4. Role Bias
        elif bias_score > 0.6:
            state = "APPROVED_WITH_WARNING"
            severity = "warning"
            rationale = "ALERTA DE SESGO: La rama favorece excesivamente a un dominio mientras descuida otros."
 
        # 5. Warning
        elif max_friction > 0.4 or avg_support < 0.7:
            state = "APPROVED_WITH_WARNING"
            severity = "warning"
            rationale = "APROXIMACIÓN CON PRECAUCIÓN: Existe fricción moderada distribuida entre los roles."
 
        return MergeGovernanceVerdict(
            state=state,
            severity=severity,
            rationale=rationale,
            blocking_roles=blocking_roles,
            required_compensations=compensations,
            suggested_missions=suggested_missions,
            persona_details=persona_details,
            merge_bias_score=bias_score
        )

    def _project_architect(self, missions: List[Any]) -> PersonaResponse:
        core_missions = [m for m in missions if any(s in ["core", "backend", "db"] for s in m.surface_affected)]
        high_risk = [m for m in core_missions if m.risk_level == "high"]
        
        friction = 0.1
        support = 0.9
        bias = "NEUTRAL"
        
        if len(high_risk) > 2:
            friction = 0.7
            support = 0.4
            
        rationale = f"Evalúa {len(core_missions)} misiones de infraestructura. "
        if len(high_risk) > 0:
            rationale += f"Detecta {len(high_risk)} puntos de riesgo estructural."
        else:
            rationale += "Estructura estable."

        proposal = None
        if friction > 0.5:
            proposal = CompensationProposal(
                type="HARDENING",
                persona_role="ARCHITECT",
                target_domain="core",
                objective="Misión de Saneamiento y Desacoplamiento de Infraestructura",
                rationale="Se han detectado múltiples puntos de riesgo estructural en la capa core. Es necesario desacoplar lógica para evitar regresiones en cascada.",
                expected_impact="Reducción de fricción arquitectónica de 0.7 a <0.3",
                suggested_risk="medium",
                suggested_constraints=["No modificar esquemas DB existentes", "Mantener compatibilidad hacia atrás"]
            )

        return PersonaResponse(
            persona_id="p_arch",
            role="ARCHITECT",
            support_score=support,
            friction_score=friction,
            domain_bias="FAVORED" if len(core_missions) > len(missions)*0.5 else "NEUTRAL",
            rationale=rationale,
            recommendation="Añadir misiones de desacoplamiento si el riesgo aumenta." if friction > 0.5 else None,
            structured_proposal=proposal
        )

    def _project_designer(self, missions: List[Any]) -> PersonaResponse:
        ui_missions = [m for m in missions if "ui" in m.surface_affected or "frontend" in m.surface_affected]
        branding_violations = [m for m in missions if "OmniShell" in m.objective] # Simple heuristic
        
        friction = 0.1
        support = 0.9
        
        if len(ui_missions) == 0:
            support = 0.6
            rationale = "Baja visibilidad UX en esta rama."
            domain_bias = "NEGLECTED"
        else:
            if len(branding_violations) > 0:
                friction = 0.6
                support = 0.5
                rationale = f"Conflictos de Branding detectados ({len(branding_violations)} instancias)."
            else:
                rationale = f"Consistente con lenguaje visual en {len(ui_missions)} misiones."
            domain_bias = "FAVORED"

        proposal = None
        if friction > 0.4:
            proposal = CompensationProposal(
                type="DESIGN",
                persona_role="DESIGNER",
                target_domain="ui",
                objective="Misión de Alineación de Branding y UX (OmniWeb Core)",
                rationale="Se han detectado inconsistencias en la nomenclatura de marca. Es imperativo consolidar bajo el estándar OMNIWEB para evitar confusión en el ecosistema.",
                expected_impact="Reducción de deriva de diseño (Design Drift) en un 80%.",
                suggested_risk="low"
            )

        return PersonaResponse(
            persona_id="p_dsgn",
            role="DESIGNER",
            support_score=support,
            friction_score=friction,
            domain_bias=domain_bias,
            rationale=rationale,
            recommendation="Normalizar nomenclatura OMNIWEB." if friction > 0.4 else None,
            structured_proposal=proposal
        )

    def _project_tester(self, missions: List[Any]) -> PersonaResponse:
        test_missions = [m for m in missions if "tests" in m.surface_affected or "validation" in m.surface_affected]
        total = len(missions)
        
        # Heuristic: if many missions but few testing ones
        friction = 0.2
        support = 0.8
        
        if total > 5 and len(test_missions) < (total * 0.2):
            friction = 0.8
            support = 0.3
            rationale = "Déficit de validación: Demasiadas misiones sin cobertura específica."
        else:
            rationale = f"Cobertura de testing adecuada ({len(test_missions)} misiones de validación)."

        proposal = None
        if friction > 0.5:
            proposal = CompensationProposal(
                type="TESTING",
                persona_role="TESTER",
                target_domain="tests",
                objective="Misión de Cobertura de Validación y Stress Testing",
                rationale="La rama contiene un volumen alto de cambios sin el correspondiente balance de misiones de validación. Se requiere hardening antes de proceder al merge.",
                expected_impact="Validación formal de los nuevos flujos y reducción de regresiones.",
                suggested_risk="low",
                suggested_constraints=["Usar Pytest para validaciones core", "Generar logs de cobertura"]
            )

        return PersonaResponse(
            persona_id="p_test",
            role="TESTER",
            support_score=support,
            friction_score=friction,
            rationale=rationale,
            recommendation="Inyectar misiones de Stress Test antes del merge." if friction > 0.5 else None,
            structured_proposal=proposal
        )

    def _project_auditor(self, missions: List[Any], branch: Any) -> PersonaResponse:
        gov_concern = 0.0
        if branch.constitutional_status == "VIOLATED":
            gov_concern = 1.0
            friction = 1.0
            support = 0.0
            rationale = "VETO: La rama viola principios constitucionales de estabilidad."
        else:
            high_risk = [m for m in missions if m.risk_level == "high"]
            gov_concern = len(high_risk) * 0.2
            friction = 0.1 + (len(high_risk) * 0.15)
            support = 0.9 - (len(high_risk) * 0.1)
            rationale = f"Vigilancia activa sobre {len(high_risk)} misiones de alto riesgo."

        proposal = None
        if friction > 0.5:
            proposal = CompensationProposal(
                type="GOVERNANCE",
                persona_role="AUDITOR",
                target_domain="governance",
                objective="Misión de Realineación Constitucional y Auditoría",
                rationale="La propuesta táctica presenta desviaciones respecto a los principios de seguridad o arquitectura definidos. Se requiere una auditoría profunda.",
                expected_impact="Asegurar el cumplimiento del 100% de la gobernanza.",
                suggested_risk="medium",
                suggested_constraints=["Incluir check de seguridad", "Validar impacto en el historial de misiones"]
            )

        return PersonaResponse(
            persona_id="p_audit",
            role="AUDITOR",
            support_score=support,
            friction_score=friction,
            governance_concern=friction,
            rationale=rationale,
            recommendation="Revisar mitigaciones en misiones de alto riesgo." if friction > 0.5 else None,
            structured_proposal=proposal
        )

persona_simulator = MultiPersonaSimulator()
