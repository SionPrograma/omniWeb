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
                    "sospechás", "prioridad de arreglo", "inspect system", "diagnose failure",
                    "estás saludable", "estás en warning", "cómo está el sistema", "estado del sistema"]
        return any(t in cmd for t in triggers) or ("saludable" in cmd and "warning" in cmd)

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        from backend.core.system_state.engine import state_engine
        from backend.core.system_state.models import SystemHealth
        
        try:
            # FORCE REFRESH to get the absolute real state
            state = await state_engine.get_state(force_refresh=True)
            
            # --- DIRECT MAPPING FROM STATE ENGINE ---
            
            # Map health to Spanish
            health_map = {
                SystemHealth.HEALTHY: "SALUDABLE",
                SystemHealth.WARNING: "WARNING",
                SystemHealth.ERROR: "CRÍTICO"
            }
            health_label = health_map.get(state.health, "DESCONOCIDO")
            
            # 1. Main Failure Identification
            main_failure = "NINGUNA DETECTADA"
            suspicious_layer = "N/A"
            evidence = "NONE"
            priority = "BAJA"
            next_action = "CONTINUAR MONITOREO"

            if state.health != SystemHealth.HEALTHY:
                # Identify failures from chips
                failed_chips = [c for c in state.chips if c.health != SystemHealth.HEALTHY]
                if failed_chips:
                    names = [c.slug.upper() for c in failed_chips]
                    main_failure = f"FALLA DETECTADA EN MÓDULO(S): {', '.join(names)}"
                    suspicious_layer = "CAPA_EJECUCIÓN_CHIPS"
                    chip_states = [f"{c.slug.upper()}:{c.health.value.upper()}" for c in failed_chips]
                    evidence = f"CHIP_SIGNALS:[{', '.join(chip_states)}]"
                    priority = "ALTA" if any(c.health == SystemHealth.ERROR for c in failed_chips) else "MEDIA"
                    next_action = "REINICIAR MÓDULOS AFECTADOS O REVISAR LOGS DE ERROR"
                
                # Check database
                elif not state.database.get("connected"):
                    main_failure = "DESCONEXIÓN DE BASE DE DATOS"
                    suspicious_layer = "CAPA_DATOS"
                    evidence = f"DB_STATE:CONNECTED=FALSE"
                    priority = "ALTA"
                    next_action = "VERIFICAR SERVICIO POSTGRES/SQLITE"

                # Check healing status
                elif state.is_healing:
                    main_failure = "SISTEMA EN PROCESO DE AUTOCURACIÓN"
                    suspicious_layer = "MOTOR_ESTABILIDAD"
                    evidence = f"HEALING_SIGNAL:PENDING_FIXES={state.pending_fixes}"
                    priority = "MEDIA"
                    next_action = "ESPERAR FINALIZACIÓN DE CICLO DE ESTABILIDAD"
                
                else:
                    main_failure = "INESTABILIDAD GENERAL DETECTADA"
                    suspicious_layer = "SISTEMA_CORE"
                    evidence = f"GLOBAL_HEALTH_VALUE:{state.health.value}"
                    priority = "MEDIA"
            
            # --- DETERMINISTIC OUTPUT ---
            # Strictly No narrative, no "I feel", no hypothesis.
            
            report = (
                f"ESTADO: {health_label}\n"
                f"FALLA PRINCIPAL: {main_failure}\n"
                f"CAPA: {suspicious_layer}\n"
                f"EVIDENCIA: {evidence}\n"
                f"PRIORIDAD: {priority}\n"
                f"SIGUIENTE ACCIÓN: {next_action}"
            )

            from backend.core.interface.visual_interface import visual_interface
            visual = visual_interface.create_visual_payload(
                "system-audit-active",
                {
                    "estado": health_label,
                    "prioridad": priority,
                    "falla_principal": main_failure,
                    "evidencia": evidence
                },
                "Real-Time Audit Mode"
            )

            return AICommandResponse(
                intent="system_audit",
                status="success",
                message=report,
                payload={"visual": visual, "state": state.dict()}
            )
        except Exception as e:
            logger.error(f"DETERMINISTIC AUDIT FAILED: {e}")
            return AICommandResponse(
                intent="system_audit",
                status="error",
                message=f"ESTADO: CRÍTICO\nFALLA PRINCIPAL: FALLO EN MOTOR DE AUDITORÍA\nCAPA: AUDIT_PROCESSOR\nEVIDENCIA: {str(e)}\nPRIORIDAD: ALTA\nSIGUIENTE ACCIÓN: REVISAR BACKEND/LOGS",
            )
