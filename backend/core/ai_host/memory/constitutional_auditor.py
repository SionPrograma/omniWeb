import logging
import re
import hashlib
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime
from backend.core.ai_host.memory.handoff_manager import ProposedMission

logger = logging.getLogger(__name__)

class ConstitutionalRule(BaseModel):
    rule_id: str
    name: str
    type: str # BRANDING, GOVERNANCE, METHOD, ARCHITECTURE
    severity: str # WARNING, BLOCKING
    description: str
    suggested_fix: str

class AuditViolation(BaseModel):
    rule_id: str
    rule_name: str
    severity: str
    message: str
    suggested_fix: str

class ConstitutionalReport(BaseModel):
    audit_id: str = Field(default_factory=lambda: hashlib.md5(str(datetime.now()).encode()).hexdigest()[:8])
    status: str # COMPLIANT, WARNING, BLOCKED
    score: float # 0.0 to 1.0
    violations: List[AuditViolation] = []
    summary: str
    generated_at: datetime = Field(default_factory=datetime.now)

class ConstitutionalAuditor:
    """
    OMNIWEB — BLOQUE: CONSTITUTIONAL SELF-AUDIT SUITE.
    Validates missions and pushes against system rules and principles.
    """
    
    def __init__(self):
        self.rules = [
            ConstitutionalRule(
                rule_id="BRAND_INTEGRITY",
                name="OmniWeb Branding Compliance",
                type="BRANDING",
                severity="WARNING",
                description="El sistema debe referirse siempre a la experiencia como OMNIWEB.",
                suggested_fix="Reemplazar 'OmniShell' por 'OmniWeb' en el título u objetivo."
            ),
            ConstitutionalRule(
                rule_id="GOV_HIGH_RISK_PIN",
                name="High Risk Governance Shield",
                type="GOVERNANCE",
                severity="BLOCKING",
                description="Toda misión de riesgo Alto o Crítico requiere un PIN de autoridad del Creador.",
                suggested_fix="Añadir un SECURITY GATE de tipo PIN a la misión."
            ),
            ConstitutionalRule(
                rule_id="METHOD_NON_DESTRUCTIVE",
                name="Non-Destructive Principle",
                type="METHOD",
                severity="BLOCKING",
                description="Las misiones deben ser aditivas y evitar el borrado masivo o refactors que rompan código estable.",
                suggested_fix="Reformular el objetivo como un 'Refactor Aditivo' o 'Hardening'."
            ),
            ConstitutionalRule(
                rule_id="NEVER_AUTO_RULE",
                name="Human-in-the-loop (NEVER_AUTO)",
                type="METHOD",
                severity="BLOCKING",
                description="No se permiten misiones que automaticen cambios críticos sin confirmación del Creador.",
                suggested_fix="Cambiar execution_style a 'with_confirmation'."
            )
        ]

    def audit_mission(self, mission: ProposedMission) -> ConstitutionalReport:
        violations = []
        
        # 1. Check Branding
        if "omnishell" in mission.objective.lower() or "omnishell" in mission.briefing_title.lower():
            rule = next(r for r in self.rules if r.rule_id == "BRAND_INTEGRITY")
            violations.append(AuditViolation(
                rule_id=rule.rule_id, rule_name=rule.name, severity=rule.severity,
                message="Se detectó el término 'OmniShell'. La constitución exige usar 'OmniWeb'.",
                suggested_fix=rule.suggested_fix
            ))

        # 2. Check Governance (Risk vs PIN)
        if mission.risk_level in ["high", "critical"]:
            has_pin = mission.gate_data and mission.gate_data.get("type") == "PIN"
            if not has_pin:
                rule = next(r for r in self.rules if r.rule_id == "GOV_HIGH_RISK_PIN")
                violations.append(AuditViolation(
                    rule_id=rule.rule_id, rule_name=rule.name, severity=rule.severity,
                    message=f"Riesgo {mission.risk_level.upper()} detectado sin protección de PIN.",
                    suggested_fix=rule.suggested_fix
                ))

        # 3. Check Method (Destructive)
        destructive_keywords = ["borrar todo", "eliminar modulo completo", "delete everything", "drop table"]
        if any(k in mission.objective.lower() for k in destructive_keywords):
            rule = next(r for r in self.rules if r.rule_id == "METHOD_NON_DESTRUCTIVE")
            violations.append(AuditViolation(
                rule_id=rule.rule_id, rule_name=rule.name, severity=rule.severity,
                message="El objetivo parece contener patrones destructivos prohibidos por el protocolo maestro.",
                suggested_fix=rule.suggested_fix
            ))

        # 4. Human-in-the-loop
        if mission.execution_style == "auto" and mission.risk_level != "low":
             rule = next(r for r in self.rules if r.rule_id == "NEVER_AUTO_RULE")
             violations.append(AuditViolation(
                rule_id=rule.rule_id, rule_name=rule.name, severity=rule.severity,
                message="No se permiten ejecuciones automáticas para misiones que no sean de riesgo bajo.",
                suggested_fix=rule.suggested_fix
            ))

        # Summary & Score
        blocking_count = len([v for v in violations if v.severity == "BLOCKING"])
        warning_count = len([v for v in violations if v.severity == "WARNING"])
        
        status = "COMPLIANT"
        if blocking_count > 0: status = "BLOCKED"
        elif warning_count > 0: status = "WARNING"
        
        score = 100 - (blocking_count * 40) - (warning_count * 15)
        score = max(0, min(100, score)) / 100.0

        summary = "Misión validada constitucionalmente."
        if status == "BLOCKED":
            summary = f"FALLO CONSTITUCIONAL: Se detectaron {blocking_count} violaciones críticas que impiden el avance."
        elif status == "WARNING":
            summary = f"OBSERVACIÓN CONSTITUCIONAL: La misión cumple pero tiene {warning_count} advertencias de estilo o branding."

        return ConstitutionalReport(
            status=status,
            score=score,
            violations=violations,
            summary=summary
        )

constitutional_auditor = ConstitutionalAuditor()
