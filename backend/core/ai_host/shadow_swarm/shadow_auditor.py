import logging
from typing import List, Dict, Any, Optional
from enum import Enum
from pydantic import BaseModel
from datetime import datetime

from .shadow_memory import shadow_memory_manager, IncidentType

logger = logging.getLogger(__name__)

class ShadowState(Enum):
    IDLE = "idle"
    ASSIGNED = "assigned"
    AUDITING = "auditing"
    REPORTED = "reported"
    BLOCKED = "blocked_by_risk"
    NEEDS_HUMAN_REVIEW = "awaiting_human_approval"

class RiskCategory(Enum):
    SHARED_LAYER_RISK = "shared_layer"
    CONTRACT_RISK = "interface_contract"
    INIT_BOOT_RISK = "boot_sequence"
    UI_SYNC_RISK = "ui_synchronization"
    PERSISTENCE_RISK = "data_persistence"
    ROUTING_RISK = "api_routing"
    STATE_INTEGRITY_RISK = "state_consistency"
    HIGH_BLAST_RADIUS = "high_impact_radius"

class ShadowType(Enum):
    AUDITOR = "auditor"
    CONSTRUCTOR = "constructor"

class ShadowAuditorReport(BaseModel):
    microtask: str
    target_layer: str
    findings: List[str]
    risk_level: str # LOW, MEDIUM, HIGH, CRITICAL
    granular_risks: List[RiskCategory] = []
    recommendations: List[str]
    no_touch_zones: List[str]
    affected_components: List[str] = []
    timestamp: datetime = datetime.now()

class ShadowAuditor(BaseModel):
    shadow_id: str
    type: ShadowType = ShadowType.AUDITOR
    mission_id: str
    assigned_microtask: str
    target_layer: str
    state: ShadowState = ShadowState.IDLE
    current_report: Optional[ShadowAuditorReport] = None
    trace_id: Optional[str] = None
    visual_context: Optional[Dict[str, Any]] = None # Pulse of multimodal evidence

    def assign(self, microtask: str, layer: str):
        self.assigned_microtask = microtask
        self.target_layer = layer
        self.state = ShadowState.ASSIGNED
        logger.info(f"[SHADOW-{self.shadow_id}] Assigned to: {microtask} on {layer}")

    async def audit(self) -> ShadowAuditorReport:
        self.state = ShadowState.AUDITING
        logger.info(f"[SHADOW-{self.shadow_id}] Starting proactive technical audit: {self.assigned_microtask}")
        
        # 1. HISTORICAL MEMORY CHECK (NUEVO BLOQUE)
        history = shadow_memory_manager.get_incidents(layer=self.target_layer)
        has_critical_history = any(i.severity in ["HIGH", "CRITICAL"] for i in history)
        
        # Proactive Detection Simulation
        risks = []
        findings = [f"Auditoría técnica de '{self.assigned_microtask}' completada."]
        components = [self.target_layer]
        
        # Incorporate Memory in Findings
        if history:
            findings.append(f"ANTECEDENTES DETECTADOS ({len(history)}): Zona con historial de incidentes ({history[0].incident_type.value}).")
            if has_critical_history:
                risks.append(RiskCategory.HIGH_BLAST_RADIUS)
                findings.append("ALERTA: Historial técnico crítico detectado en esta capa.")

        if "core" in self.target_layer or "logic" in self.assigned_microtask.lower():
            risks.append(RiskCategory.SHARED_LAYER_RISK)
            findings.append("Detectada dependencia en capa compartida crítica.")
            components.append("backend/core/engine")
            
        if "ui" in self.assigned_microtask.lower() or "frontend" in self.target_layer:
            risks.append(RiskCategory.UI_SYNC_RISK)
            findings.append("Riesgo de desincronización de estado en UI real-time.")
            
        # 3. MULTIMODAL VERIFICATION (PHASE 21)
        if self.visual_context:
            anns = self.visual_context.get("annotations", [])
            points = [a for a in anns if a.get('type') == 'point']
            hyp = self.visual_context.get("hypothesis", {})
            
            if points:
                findings.append(f"VERIFICACIÓN VISUAL: Priorizando análisis en {len(points)} puntos señalados por el Creator.")
            
            if hyp.get("roadmap_hint"):
                findings.append(f"ORIENTACIÓN TÉCNICA: {hyp['roadmap_hint']}")
            
            if hyp.get("component") and hyp["component"] != "unknown":
                components.append(hyp["component"])
                findings.append(f"COMPONENTE SOSPECHOSO: {hyp['component']}")
            
            if hyp.get("issue_type"):
                 findings.append(f"TIPO DE INCIDENTE ESTIMADO: {hyp['issue_type']}")

            for ann in anns:
                if ann.get('comment'):
                    findings.append(f"FOCO ANOTADO: {ann['comment']}")

        # Elevate risk if historical friction is present
        base_level = "HIGH" if len(risks) > 1 else ("MEDIUM" if risks else "LOW")
        if history and base_level != "HIGH":
            base_level = "MEDIUM"
        if has_critical_history:
            base_level = "HIGH"

        report = ShadowAuditorReport(
            microtask=self.assigned_microtask,
            target_layer=self.target_layer,
            findings=findings,
            risk_level=base_level,
            granular_risks=risks,
            recommendations=[f"Utilizar estrategia conservadora para {self.target_layer}." + (" (Historial detectado)" if history else "")],
            no_touch_zones=["core/engine", "backend/security"],
            affected_components=components
        )
        
        self.current_report = report
        self.state = ShadowState.REPORTED
        return report

class ShadowAuditorManager:
    """
    Manages the lifecycle and state of Shadow Auditors.
    """
    def __init__(self):
        self.active_shadows: Dict[str, ShadowAuditor] = {}

    def spawn_auditor(self, mission_id: str, microtask: str, layer: str) -> ShadowAuditor:
        shadow_id = f"shadow_audit_{len(self.active_shadows) + 1:03d}"
        auditor = ShadowAuditor(
            shadow_id=shadow_id,
            mission_id=mission_id,
            assigned_microtask=microtask,
            target_layer=layer,
            state=ShadowState.ASSIGNED
        )
        self.active_shadows[shadow_id] = auditor
        return auditor

    def get_shadows_for_mission(self, mission_id: str) -> List[ShadowAuditor]:
        return [s for s in self.active_shadows.values() if s.mission_id == mission_id]

shadow_auditor_manager = ShadowAuditorManager()
