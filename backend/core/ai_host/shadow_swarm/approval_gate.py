import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from .shadow_constructor import ShadowConstructor, ConstructorState, ShadowConstructorProposal
from .shadow_auditor import ShadowState

logger = logging.getLogger(__name__)

class GateStatus(Enum):
    PROPOSED = "proposed"
    AWAITING_AUDIT = "awaiting_audit"
    AWAITING_HUMAN = "awaiting_human_approval"
    BLOCKED_BY_RISK = "blocked_by_risk"
    ESCALATED = "escalated"
    EXTREME = "extreme_risk_escalated"
    READY_FOR_APPLY = "ready_for_apply"
    REJECTED = "rejected"
    AWAITING_PIN = "awaiting_pin_override"

class ApprovalGateDecision(BaseModel):
    proposal_id: str
    status: GateStatus
    requires_approval: bool = True
    danger_level: str # CRITICAL, HIGH, MEDIUM, LOW
    affected_targets: List[str]
    rollback_note: str
    is_safe: bool
    blocking_reason: Optional[str] = None
    audit_confirmed: bool = False
    human_approval_required: bool = True
    checkpoint_required: bool = True
    result_summary: str

class ApprovalGate:
    """
    Governance layer for validating shadow constructor proposals.
    Ensures that no change passes without structured validation.
    """
    
    def __init__(self, policy_engine: Any = None):
        self.policy_engine = policy_engine
        self.sensitive_layers = [
            "backend/core", "core/kernel", "security/auth", 
            "core/permissions", "infrastructure/db", "core/ai_host", 
            "core/orchestration", ".env", "main.py"
        ]

    def evaluate_proposal(self, constructor: "ShadowConstructor") -> ApprovalGateDecision:
        # (Preserving evaluate_proposal but ensuring it calls the unified logic)
        proposal = constructor.proposal
        if not proposal:
             return self.execute_governance_check(
                 intent=constructor.assigned_microtask,
                 targets=[constructor.target_layer or "shadow"],
                 action_type="shadow_draft",
                 risk_hint="UNKNOWN"
             )
        
        return self.execute_governance_check(
            intent=constructor.assigned_microtask,
            targets=[proposal.target_file] if proposal.target_file else [constructor.target_layer or "shadow"],
            action_type="mutation",
            risk_hint=proposal.risk_assessment,
            proposal_id=constructor.shadow_id,
            audit_confirmed=constructor.auditor_note is not None
        )

    def execute_governance_check(self, intent: str, targets: List[str], action_type: str, risk_hint: str = "MEDIUM", proposal_id: str = "gen_action", audit_confirmed: bool = False) -> ApprovalGateDecision:
        """
        Unified Governance Entry Point for ALL sensitive actions (Bloque 3).
        """
        # 1. Sensitivity Detection
        is_sensitive = any(any(layer in (t or "") for layer in self.sensitive_layers) for t in targets)
        is_risky_action = action_type.lower() in ["restart", "delete", "mutation", "remediation", "patch"]
        
        # 2. Risk Calculation
        danger_level = risk_hint.upper()
        
        # 2.1 CONSERVATIVE MODE ELEVATION (Phase 18)
        is_conservative = False
        active_mission = None
        try:
             from backend.core.ai_host.memory.mission_manager import mission_manager
             active_mission = mission_manager.get_active_mission()
             if active_mission and active_mission.parameters.get("conservative_mode"):
                  is_conservative = True
                  logger.info("[APPROVAL_GATE] Creator Conservative Mode: Elevating risk thresholds.")
                  if danger_level == "LOW": danger_level = "MEDIUM"
                  elif danger_level == "MEDIUM": danger_level = "HIGH"
                  elif danger_level == "HIGH": danger_level = "CRITICAL"
        except: pass

        if is_sensitive:
            danger_level = "CRITICAL" if any("core" in (t or "") for t in targets) else "HIGH"
        elif is_risky_action and danger_level == "LOW":
            danger_level = "MEDIUM"

        # 3. MEGAPROMPT SCOPE LOCK INTEGRATION (CAPA 2 & 5)
        status = GateStatus.AWAITING_HUMAN
        blocking_reason = None
        is_safe = True
        
        try:
            if not active_mission:
                 from backend.core.ai_host.memory.mission_manager import mission_manager
                 active_mission = mission_manager.get_active_mission()

            from backend.core.ai_host.orchestration.scope_lock import ScopeLock
            
            # --- PHASE 19 & 21: RICH CONSTRAINT + AUTONOMY BOUNDARIES ---
            params = active_mission.parameters if active_mission else {}
            risk_budget = params.get("risk_budget", 10.0)
            risk_consumed = params.get("risk_consumed", 0.0)
            
            # PHASE 21: Cooldown Check
            if params.get("cooldown_active"):
                 status = GateStatus.BLOCKED_BY_RISK
                 blocking_reason = "ESTABILIZACIÓN EN CURSO: El sistema está enfriándose tras una descarga de mutaciones. Esperá un momento."
                 is_safe = False
                 logger.warning(f"[APPROVAL_GATE] Blocked mutation during active cooldown.")

            # Autonomy Check
            if is_safe and risk_consumed >= risk_budget:
                 status = GateStatus.BLOCKED_BY_RISK
                 blocking_reason = f"AUTONOMÍA EXCEDIDA: Presupuesto de riesgo agotado ({risk_consumed}/{risk_budget}). Requiere inyección de autoridad."
                 is_safe = False
                 logger.warning(f"[APPROVAL_GATE] Blocked mutation due to risk budget exhaustion.")

            if is_safe:
                forbidden_p = params.get("forbidden_paths", [])
                forbidden_l = params.get("forbidden_layers", [])
                frozen_p = params.get("frozen_paths", [])
                frozen_l = params.get("frozen_layers", [])
                allowed_p = params.get("allowed_paths", [])
                aggressiveness = params.get("aggressiveness", "balanced")

                for target in targets:
                    target_str = str(target or "")
                    
                    # 0.1 Frozen Sector Check (Phase 21)
                    if any(p in target_str for p in frozen_p):
                        status = GateStatus.BLOCKED_BY_RISK
                        blocking_reason = f"SECTOR CONGELADO: El Creador pausó cambios en '{target_str}'"
                        is_safe = False
                        self._trigger_drift_check(active_mission, target_str, "CONGELADO")
                        break
                    
                    # 0.2 Frozen Layer Check (Phase 21)
                    if any(l in target_str.lower() for l in frozen_l):
                        status = GateStatus.BLOCKED_BY_RISK
                        blocking_reason = f"CAPA CONGELADA: El Creador pausó la superficie '{target_str}'"
                        is_safe = False
                        self._trigger_drift_check(active_mission, target_str, "CAPA_CONGELADA")
                        break

                    # 1. Path Blocking (Phase 19)
                    if any(p in target_str or target_str in p for p in forbidden_p):
                        status = GateStatus.BLOCKED_BY_RISK
                        blocking_reason = f"ZONA PROHIBIDA: El Creador restringió el archivo/ruta '{target_str}'"
                        is_safe = False
                        self._trigger_drift_check(active_mission, target_str, "PROHIBIDO")
                        break
                    
                    # 2. Layer Blocking (Phase 19)
                    if any(l in target_str.lower() for l in forbidden_l):
                        status = GateStatus.BLOCKED_BY_RISK
                        blocking_reason = f"CAPA PROHIBIDA: El Creador restringió la superficie '{target_str}'"
                        is_safe = False
                        break
                    
                    # 3. Allowed Path Filter
                    if allowed_p and not any(p in target_str or target_str in p for p in allowed_p):
                        status = GateStatus.BLOCKED_BY_RISK
                        blocking_reason = f"FUERA DE ALCANCE: El Creador limitó la misión. '{target_str}' no permitido."
                        is_safe = False
                        break
                    
                    # 4. Aggressiveness Constraint (Surgical Mode)
                    if aggressiveness == "surgical" and action_type == "mutation" and active_mission:
                         if not any(t in target_str for t in active_mission.related_targets):
                              status = GateStatus.BLOCKED_BY_RISK
                              blocking_reason = f"MODO QUIRÚRGICO: Bloqueada mutación fuera de los targets declarados."
                              is_safe = False
                              break

            # Skip deeper checks if already blocked
            if is_safe:
                # Conservative Guard
                if is_conservative and danger_level in ["HIGH", "CRITICAL"] and action_type == "mutation":
                      status = GateStatus.AWAITING_HUMAN
                      logger.info(f"[APPROVAL_GATE] Conservative guard forced AWAITING_HUMAN.")

            if active_mission and "plan_data" in active_mission.context_snap:
                plan_data = active_mission.context_snap["plan_data"]
                # We extract the compiled mission if present
                from backend.core.ai_host.orchestration.prompt_compiler import CompiledMission
                # Handle both dict and object
                if isinstance(plan_data, dict) and "compiled_mission" in plan_data:
                    compiled = CompiledMission(**plan_data["compiled_mission"])
                    lock = ScopeLock(compiled)
                    
                    for target in targets:
                        check = lock.validate_action(action_type, target, intent)
                        if not check["is_valid"]:
                            status = GateStatus.BLOCKED_BY_RISK
                            blocking_reason = f"DESVIACIÓN DE MISIÓN: {check['violations'][0]}"
                            is_safe = False
                            logger.error(f"[SCOPE_LOCK_VIOLATION] Blocked {action_type} on {target}: {blocking_reason}")
                            break
        except Exception as e:
            logger.warning(f"[APPROVAL_GATE] ScopeLock check failed (continuing with normal rules): {e}")

        # 4. Sensitivity Determination
        if is_safe:
            # PHASE 21: Extreme Risk & Creator PIN Check
            if danger_level in ["EXTREME", "CRITICAL"] and not params.get("hard_override_granted"):
                 # Core changes or extreme risk always require PIN if under certain conditions
                 if any("core" in str(t or "").lower() for t in targets) or danger_level == "EXTREME":
                      status = GateStatus.AWAITING_PIN
                      blocking_reason = "AUTORIDAD REFORZADA: Esta acción compromete el núcleo o tiene riesgo EXTREMO. Requiere PIN del Creador."
                      is_safe = False
                      logger.warning(f"[APPROVAL_GATE] Extreme risk action escalated to PIN override.")

            if is_safe:
                if danger_level == "EXTREME":
                    status = GateStatus.EXTREME
                    blocking_reason = "PELIGRO EXTREMO: Acción bloqueada por política de seguridad."
                    is_safe = False
                elif is_sensitive and not audit_confirmed and action_type == "mutation":
                    status = GateStatus.AWAITING_AUDIT
                    blocking_reason = "Falta validación técnica (Shadow Audit) previa."
                    is_safe = False
                elif is_sensitive:
                    status = GateStatus.ESCALATED
                    is_safe = False
        
        # 5. Final Metadata (Bloque 3)
        rollback = f"Restaurar configuración previa o checkpoint de seguridad."
        if proposal_id != "gen_action" and not proposal_id.startswith("swarm"):
            rollback = f"Restaurar desde checkpoint `.shadow_checkpoints/before_{proposal_id}_*.bak`"

        summary = f"GATED: {status.value.upper()} ({danger_level})"
        if is_safe and status == GateStatus.AWAITING_HUMAN:
            summary = "LISTO PARA APROBACIÓN HUMANA"
        
        # --- PHASE 21: CONSUME RISK BUDGET ---
        if is_safe or status in [GateStatus.AWAITING_HUMAN, GateStatus.ESCALATED, GateStatus.AWAITING_AUDIT]:
             try:
                  from backend.core.ai_host.memory.mission_manager import mission_manager
                  risk_weights = {"CRITICAL": 2.0, "HIGH": 1.0, "MEDIUM": 0.5, "LOW": 0.1}
                  risk_amount = risk_weights.get(danger_level, 0.5)
                  mission_manager.track_risk_consumption(risk_amount)
             except: pass

        # --- PHASE 21: COOLDOWN TRACKING ---
        if is_safe and action_type == "mutation":
             try:
                  from backend.core.ai_host.memory.mission_manager import mission_manager
                  mission = mission_manager.get_active_mission()
                  if mission:
                       count = mission.parameters.get("consecutive_mutations", 0) + 1
                       mission.parameters["consecutive_mutations"] = count
                       if count >= 5:
                            mission_manager.trigger_cooldown()
                       else:
                            mission_manager.save_mission(mission)
             except: pass

        return ApprovalGateDecision(
            proposal_id=proposal_id,
            status=status,
            requires_approval=True,
            danger_level=danger_level,
            affected_targets=targets,
            rollback_note=rollback,
            is_safe=is_safe,
            blocking_reason=blocking_reason,
            audit_confirmed=audit_confirmed,
            human_approval_required=True,
            checkpoint_required=True,
            result_summary=summary
        )


    def _trigger_drift_check(self, mission: Any, target: str, reason: str):
        """Accumulates and reports constitutional violations (Phase 21)."""
        if not mission: return
        
        try:
            from backend.core.ai_host.governance.drift_detector import drift_detector, DriftAlert, DriftType, DriftSeverity
            
            violations = mission.context_snap.get("drift_violations", 0) + 1
            mission.context_snap["drift_violations"] = violations
            
            severity = DriftSeverity.INFO
            if violations == 1: severity = DriftSeverity.WARNING
            if violations >= 3: severity = DriftSeverity.CRITICAL
            
            alert = DriftAlert(
                type=DriftType.GOVERNANCE,
                severity=severity,
                message=f"Erosión de gobernanza: Intento de acceso a zona {reason}.",
                targets=[target],
                suggestion="Revisar actividad persistente o congelar zona completa."
            )
            drift_detector.record_drift_event(alert)
        except Exception as e:
            logger.error(f"[APPROVAL_GATE] Drift check failed: {e}")

    def get_governance_health(self, mission: Any) -> Dict[str, Any]:
        """Synthesizes all governance signals into a single health indicators (Phase 21)."""
        if not mission: return {"status": "UNKNOWN", "score": 0}
        
        params = mission.parameters
        alerts = mission.context_snap.get("drift_alerts", [])
        risk_consumed = params.get("risk_consumed", 0.0)
        risk_budget = params.get("risk_budget", 10.0)
        
        # 1. Determine Master Status (Priority Ladder)
        health = {
            "status": "STEADY",
            "color": "#00ff88",
            "recommendation": "Continuar con la misión normal.",
            "active_blocks": []
        }
        
        # PIN Required (Top Priority)
        if params.get("hard_override_granted") is False and mission.status == MissionStatus.PAUSED:
             # Check if blocked by PIN
             if any("PIN" in r for r in mission.blocked_reasons):
                  health.update({"status": "LOCKDOWN", "color": "#ff0055", "recommendation": "INYECTAR PIN de autoridad para reanudar núcleo."})
                  health["active_blocks"].append("Creator PIN")
        
        # Drift Critical
        elif any(a.get("severity") == "CRITICAL" for a in alerts):
             health.update({"status": "EROSIÓN CRÍTICA", "color": "#ff0055", "recommendation": "Auditar deriva arquitectónica inmediatamente."})
             health["active_blocks"].append("Drift Detector")

        # Risk Exceeded
        elif risk_consumed >= risk_budget:
             health.update({"status": "AUTONOMÍA AGOTADA", "color": "#ffaa00", "recommendation": "Ampliar presupuesto de riesgo o finalizar tanda."})
             health["active_blocks"].append("Autonomy Boundary")

        # Stabilization / Cooldown
        elif params.get("cooldown_active"):
             health.update({"status": "ENFRIAMIENTO", "color": "#00e5ff", "recommendation": "Asegurar estabilidad antes de la siguiente wave."})
             health["active_blocks"].append("Shadow Cooldown")

        # Drift Warning
        elif any(a.get("severity") == "WARNING" for a in alerts):
             health.update({"status": "DESVIACIÓN LEVE", "color": "#ffcc00", "recommendation": "Revisar políticas de acceso o snapshots."})
             health["active_blocks"].append("Drift Warning")

        # Guarded (Any constraints active)
        elif params.get("forbidden_paths") or params.get("frozen_paths"):
             health.update({"status": "BAJO GUARDIA", "color": "#00ffcc", "recommendation": "Misión operando bajo restricciones constitucionales."})
             health["active_blocks"].append("Constraint Mapping")
        
        return health

# Singleton instance
approval_gate = ApprovalGate(policy_engine=None)
