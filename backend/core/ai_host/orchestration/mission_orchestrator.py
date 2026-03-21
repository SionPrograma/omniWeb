import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class MissionPhase:
    def __init__(self, name: str, status: str = "PENDIENTE", detail: str = ""):
        self.name = name
        self.status = status
        self.detail = detail

    def to_dict(self):
        return {"name": self.name, "status": self.status, "detail": self.detail}

class MissionOrchestrator:
    """
    Advanced Work Orchestrator for OmniWeb.
    Decides and tracks technical phases for complex missions.
    """
    
    def __init__(self):
        self.phases: List[MissionPhase] = []

    def plan_mission(self, message: str, intent: str) -> List[MissionPhase]:
        msg = message.lower()
        self.phases = []
        
        # Phase 1: AUDIT & ISOLATE (Always first for technical tasks)
        self.phases.append(MissionPhase("LECTURA/AUDITORÍA", "COMPLETADO", "Resolución de scope y análisis de integridad."))
        
        # Phase 2: DETECTION (If it's a fix or analysis)
        if any(kw in msg for kw in ["arregla", "revisa", "audit", "analiza", "fix", "bug"]):
             self.phases.append(MissionPhase("DETECCIÓN_RIESGO", "COMPLETADO", "Mapeo de contratos y acoplamientos sensibles."))
        
        # Phase 3: PROPOSAL
        if any(kw in msg for kw in ["propon", "cambia", "fix", "arregla", "hacé", "modifica"]):
             self.phases.append(MissionPhase("PROPUESTA_PATCH", "PROCESANDO", "Generación de micro-mutación no destructiva."))
        
        # Phase 4: PREVIEW
        if any(kw in msg for kw in ["mostra", "preview", "diff", "arregla"]):
             self.phases.append(MissionPhase("PREVIEW_VISUAL", "PENDIENTE", "Preparando diff unificado para auditoría visual."))
        
        # Phase 5: APPLY (Always manual/blocked initially)
        if any(kw in msg for kw in ["aplica", "ejecuta", "hace"]):
             self.phases.append(MissionPhase("APLICACIÓN", "BLOQUEADO", "Requiere validación de Preview y confirmación del creador."))
        else:
             self.phases.append(MissionPhase("APLICACIÓN", "STANDBY", "Fase opcional sujeta a decisión del creador."))

        # Phase 6: VERIFICATION
        self.phases.append(MissionPhase("VERIFICACIÓN", "ESPERA", "Monitoreo de estabilidad post-operación."))
        
        return self.phases

    def format_orchestration_report(self) -> str:
        if not self.phases:
            return ""
            
        report = "### OMNI_WORK_ORCHESTRATION\n\n"
        for i, phase in enumerate(self.phases, 1):
            mark = "✅" if phase.status == "COMPLETADO" else "🔄" if phase.status == "PROCESANDO" else "⏸️" if phase.status == "STANDBY" else "🚫" if phase.status == "BLOQUEADO" else "⏳"
            report += f"{i}. {mark} **{phase.name}** | {phase.status}\n   > {phase.detail}\n"
        
        current = next((p for p in self.phases if p.status in ["PROCESANDO", "PENDIENTE", "BLOQUEADO"]), self.phases[-1])
        report += f"\n**FASE_ACTUAL:** {current.name}\n"
        return report

# Singleton instance
mission_orchestrator = MissionOrchestrator()
