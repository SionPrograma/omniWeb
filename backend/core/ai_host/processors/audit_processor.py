from typing import Dict, Any, Optional, List
import logging
from .base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class AuditProcessor(CommandProcessor):
    """
    Conversational System Auditor - STRICT SIGNAL-BASED VERSION.
    Provides structured system health reports based on real runtime signals.
    """

    async def can_handle(self, command: str) -> bool:
        cmd = command.lower().strip()
        triggers = ["auditá", "audita", "audit", "qué está fallando", "qué falla", "diagnóstica", 
                    "diagnostica", "revisa el sistema", "qué capa falla", "qué modulo falla", 
                    "sospechás", "prioridad de arreglo", "inspect system", "diagnose failure"]
        return any(t in cmd for t in triggers)

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        from backend.core.system_state.engine import state_engine
        from backend.core.system_state.models import SystemHealth
        from backend.core.master_logbook.manager import master_logbook_manager
        from backend.core.master_logbook.models import MasterLogbookFilter, EntryType, Priority
        
        try:
            state = await state_engine.get_state()
            
            # --- SIGNAL GATHERING ---
            
            # 1. Fetch recent audit/event logs
            recent_logs = []
            for etype in [EntryType.SYSTEM_AUDIT, EntryType.SYSTEM_EVENT, EntryType.BUG]:
                recent_logs.extend(master_logbook_manager.get_entries(
                    filters=MasterLogbookFilter(type=etype), 
                    limit=5
                ))
            
            # Sort by timestamp
            recent_logs.sort(key=lambda x: x.timestamp, reverse=True)
            
            # --- ANALYSIS ENGINE ---
            
            # Default values
            health_label = state.health.value.upper()
            main_failure = "NINGUNA DETECTADA" if state.health == SystemHealth.HEALTHY else "INESTABILIDAD EN SUBSISTEMAS"
            suspicious_layer = "UNKNOWN"
            evidence = f"Chips: {len(state.chips)}"
            priority = "MEDIUM" if state.health != SystemHealth.HEALTHY else "LOW"
            next_action = "CONTINUAR MONITOREO"
            
            # A) Identify Critical Signals from Logs
            evasion_log = next((l for l in recent_logs if "evasion_detected" in l.content or "evasion_detected" in str(l.metadata)), None)
            general_error = next((l for l in recent_logs if l.priority in [Priority.HIGH, Priority.CRITICAL]), None)
            
            if evasion_log:
                main_failure = "CONTAMINACIÓN COGNITIVA / EVASIÓN EN GENERACIÓN DE RESPUESTA"
                suspicious_layer = "AI HOST / RESPONSE GENERATION LAYER"
                evidence = "DETECTADO EVENTO: evasion_detected EN MASTER LOGBOOK"
                priority = "HIGH"
                next_action = "REVISAR FILTROS DE SALIDA Y UNIFICACIÓN DE RESPUESTAS"
            elif general_error:
                main_failure = general_error.content.upper()
                suspicious_layer = general_error.chip_reference.upper() if general_error.chip_reference else "CORE / SYSTEM"
                evidence = f"ENTRADA DE LOGBOOK TIPO {general_error.type.value.upper()}"
                priority = general_error.priority.value.upper()
                next_action = "INVESTIGAR LOGS ESPECÍFICOS DEL MÓDULO"
                
            # B) Health Overrides from state_engine
            elif state.health == SystemHealth.ERROR:
                failed_chips = [c.slug for c in state.chips if c.health == SystemHealth.ERROR]
                if failed_chips:
                    main_failure = f"FALLA CRÍTICA EN CHIP(S): {', '.join(failed_chips).upper()}"
                    suspicious_layer = "CHIP RUNTIME / REGISTRY"
                    evidence = f"{len(failed_chips)} CHIPS EN ESTADO ERROR"
                    priority = "HIGH"
                    next_action = "REINICIALIZAR MÓDULOS DE BACKEND PARA LOS CHIPS AFECTADOS"
            
            # C) Specific Shell Audit (User Request Context)
            if ("panel" in msg.lower() or "drawer" in msg.lower()) and "drawer" not in main_failure.lower():
                 # Layer specific diagnostic for the reported drawer issue
                 main_failure = "INTERACCIÓN DE AUDIT DRAWER BLOQUEADA O INACTIVA"
                 suspicious_layer = "FRONTEND SHELL / CSS / EVENT LISTENERS"
                 evidence = "CONFLICTO DE Z-INDEX CON DASHBOARD OVERLAYS"
                 priority = "MEDIUM"
                 next_action = "VERIFICAR AUDIT_DRAWER.CSS Y CREATOR.JS SETUP"

            # --- STRICT FORMAT OUTPUT ---
            # No Markdown headers, no filler, just pure structured text key-value
            
            report = (
                f"ESTADO: {health_label}\n"
                f"FALLA PRINCIPAL: {main_failure}\n"
                f"CAPA: {suspicious_layer}\n"
                f"EVIDENCIA: {evidence}\n"
                f"PRIORIDAD: {priority}\n"
                f"SIGUIENTE ACCIÓN: {next_action}"
            )

            # Optional visual remains in payload for UI if shell permits, 
            # but 'message' is strictly text as requested.
            from backend.core.interface.visual_interface import visual_interface
            visual = visual_interface.create_visual_payload(
                "system-audit-active",
                {"status": priority.lower(), "failure": main_failure},
                "Stict Audit Mode"
            )

            return AICommandResponse(
                intent="system_audit",
                status="success",
                message=report,
                payload={"visual": visual}
            )
        except Exception as e:
            logger.error(f"STRICT AUDIT FAILED: {e}")
            return AICommandResponse(
                intent="system_audit",
                status="error",
                message=f"ESTADO: ERROR\nFALLA PRINCIPAL: CRASH EN PROCESADOR DE AUDITORÍA\nCAPA: SYSTEM_AUDIT_SERVICE\nEVIDENCIA: {str(e)}\nPRIORIDAD: CRITICAL\nSIGUIENTE ACCIÓN: REVISAR BACKEND/MAIN.PY LOGS",
            )
