import logging
from typing import List, Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class MissionPhase:
    def __init__(self, name: str, status: str = "PENDIENTE", detail: str = "", source: str = "text"):
        self.name = name
        self.status = status
        self.detail = detail
        self.source = source

    def to_dict(self):
        return {"name": self.name, "status": self.status, "detail": self.detail, "source": self.source}

class MissionOrchestrator:
    """
    Advanced Work Orchestrator for OmniWeb.
    Decides and tracks technical phases for complex missions.
    Voice-Aware (Block 8 Enhancement).
    """
    
    def __init__(self):
        self.phases: List[MissionPhase] = []
        self.is_voice = False

    def plan_mission(self, message: str, intent: str, interpretation: Optional[Dict[str, Any]] = None, source: str = "text") -> List[MissionPhase]:
        msg = message.lower()
        self.phases = []
        self.is_voice = (source == "voice")
        
        # 0. STRUCTURED DATA EXTRACTION
        from backend.core.ai_host.memory.mission_manager import mission_manager
        active_mission_state = mission_manager.get_active_mission()
        
        mission = None
        if interpretation and "structured_mission" in interpretation:
             mission = interpretation["structured_mission"]
             
        # Phase 0: INITIALIZATION (Objective / Voice)
        if self.is_voice:
             self.phases.append(MissionPhase("VOICE_READY", "COMPLETADO", "Entrada natural persistente procesada.", source="voice"))
        
        obj = mission["objective"] if mission else "Misión técnica"
        self.phases.append(MissionPhase("OBJETIVO_ESTABLECIDO", "COMPLETADO", f"Intención: {obj}"))

        # Phase 1: SCOPE & SURFACE
        surfaces = mission["surface_affected"] if mission else []
        if active_mission_state:
             active_mission_state.related_targets = surfaces
        surface_str = ", ".join(surfaces) if surfaces else "Indeterminado"
        self.phases.append(MissionPhase("FOCO_TÉCNICO", "COMPLETADO", f"Superficie: [{surface_str}]"))

        # Phase 2: GOVERNANCE & CONSTRAINTS (New Mandatory Layer)
        if mission and mission["constraints"]:
             cons = " | ".join(mission["constraints"])
             self.phases.append(MissionPhase("LÍMITES_OPERATIVOS", "COMPLETADO", f"Restricciones: {cons}"))
        
        # Phase 3: RISK ASSESSMENT (High risk adds extra security phase)
        session = active_mission_state.authority_session if active_mission_state else {}
        is_overridden = False
        
        if session.get("authority_granted"):
            expires_at_str = session.get("authority_expires_at")
            if expires_at_str:
                expires_at = datetime.fromisoformat(expires_at_str)
                if expires_at > datetime.now():
                    is_overridden = True
                else:
                    # Session Expired (Phase 82) - Hardening
                    active_mission_state.authority_session["authority_granted"] = False
                    active_mission_state.authority_session["authority_invalidated_reason"] = "authority_session_timeout"
                    try:
                        from backend.core.ai_host.memory.mission_telemetry import mission_telemetry
                        mission_telemetry.record_event(
                            active_mission_state.mission_id,
                            "authority_session_expired",
                            "La autoridad manual del Creador ha expirado por tiempo (+10m). Reinicie override si es necesario.",
                            severity="INFO",
                            source_actor="System"
                        )
                        from backend.core.ai_host.memory.mission_manager import mission_manager
                        mission_manager.save_mission(active_mission_state)
                    except: pass

        risk = mission["risk_level"].upper() if mission else "BAJO"
        if risk == "HIGH":
             status = "COMPLETADO" if is_overridden else "BLOQUEADO"
             detail = "Autorizado manualmente por el Creador (SESIÓN ACTIVA)." if is_overridden else "RIESGO ALTO: Requiere confirmación manual para cada paso."
             self.phases.append(MissionPhase("COGNITIVE_GOVERNANCE_LOCK", status, detail, source="governance"))
        else:
             self.phases.append(MissionPhase("EVALUACIÓN_RIESGO", "COMPLETADO", f"Nivel: {risk}"))

        # Phase 4: EXECUTION STRATEGY
        style = mission["execution_style"] if mission else "standard"
        if "audit_first" in style:
             self.phases.append(MissionPhase("AUDITORÍA_PREVIA", "PROCESANDO", "Modo Inspección Activo. No se realizarán mutaciones sin reporte previo."))
        elif "surgical_patch" in style:
             self.phases.append(MissionPhase("PATCH_QUIRÚRGICO", "PROCESANDO", "Aplicando criterio de mínima intervención."))
        else:
             self.phases.append(MissionPhase("PLAN_DE_EJECUCIÓN", "PROCESANDO", "Generando pasos de implementación estándar."))

        # Phase 5: STOP CONDITIONS (If specified)
        if mission and mission["stop_conditions"]:
             stops = " | ".join(mission["stop_conditions"])
             self.phases.append(MissionPhase("CONDICIONES_DE_FRENO", "COMPLETADO", f"Escalar si: {stops}"))

        # Phase 6: PROPOSAL & PREVIEW (Standard)
        self.phases.append(MissionPhase("PREVIEW_VISUAL", "PENDIENTE", "Preparando diff para auditoría del creador."))
        
        # Phase 7: FINAL GATE
        conf = "CON_CONFIRMACIÓN" if (mission and "with_confirmation" in mission["execution_style"]) else "ESTÁNDAR"
        self.phases.append(MissionPhase("APLICACIÓN", "STANDBY", f"Puerta de salida: {conf}"))

        return self.phases

    def format_orchestration_report(self) -> str:
        if not self.phases:
            return ""
            
        header = "### OMNI_WORK_ORCHESTRATION"
        if self.is_voice:
             header = "### OMNI_VOICE_CONTROL_CENTER 🎙️"
             
        report = f"{header}\n\n"
        for i, phase in enumerate(self.phases, 1):
             mark = "✅" if phase.status == "COMPLETADO" else "🔄" if phase.status == "PROCESANDO" else "⏸️" if phase.status == "STANDBY" else "🚫" if phase.status == "BLOQUEADO" else "⏳"
             report += f"{i}. {mark} **{phase.name}** | {phase.status}\n   > {phase.detail}\n"
        
        current = next((p for p in self.phases if p.status in ["PROCESANDO", "PENDIENTE", "BLOQUEADO"]), self.phases[-1])
        report += f"\n**FASE_ACTUAL:** {current.name}\n"
        
        if self.is_voice:
             report += "\n---\n*Omni está escuchando... Di 'aplicar' o 'descartar' para continuar.*"
             
        return report

# Singleton instance
mission_orchestrator = MissionOrchestrator()
