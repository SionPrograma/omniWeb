import logging
from typing import Dict, Any, Optional
from .base import CommandProcessor, AICommandResponse
from backend.core.system_state.engine import state_engine
from backend.core.system_state.models import SystemHealth

logger = logging.getLogger(__name__)

class StatusProcessor(CommandProcessor):
    """
    AI Host Processor for System Status and Unified State Queries.
    Phase 10: Unified System State Core.
    """

    async def can_handle(self, command: str) -> bool:
        terms = ["estado del sistema", "cómo está el sistema", "system status", "health", "salud", "chips", "módulos", "modules"]
        cmd = command.lower()
        # Avoid conflict with healing processor if it's strictly about fixing
        return any(term in cmd for term in terms)

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = command.lower()
        from ..sessions import session_state
        lang = session_state.language
        
        state = await state_engine.get_state()
        
        # 1. Detail Chip Query
        if any(x in cmd for x in ["chips", "módulos", "modules"]):
            return self._format_chips_response(state, lang)
        
        # 2. General Health / Status
        return self._format_general_status(state, lang)

    def _format_general_status(self, state, lang: str) -> AICommandResponse:
        health_icon = "PASS"
        if state.health == SystemHealth.WARNING: health_icon = "WARN"
        elif state.health == SystemHealth.ERROR: health_icon = "FAIL"
        
        if lang == "es":
            healing_note = "\n\n✨ El sistema se está auto-curando..." if state.is_healing else ""
            message = (
                f"ESTADO DEL SISTEMA UNIFICADO [{health_icon}]\n"
                f"- Versión: {state.version} ({state.git_branch})\n"
                f"- Salud Global: {state.health.value.upper()}\n"
                f"- AI Host: {state.ai_host['status'].upper()}\n"
                f"- Base de Datos: {state.database['status'].upper()}\n"
                f"- Chips Activos: {len(state.chips)}\n"
                f"- Tiempo Activo: {int(state.uptime_seconds // 3600)}h {int((state.uptime_seconds % 3600) // 60)}m\n"
                f"{healing_note}\n\n"
                f"¿Deseas ver la lista de chips o los últimos resultados de auditoría?"
            )
        else:
            healing_note = "\n\n✨ The system is currently self-healing..." if state.is_healing else ""
            message = (
                f"UNIFIED SYSTEM STATUS [{health_icon}]\n"
                f"- Version: {state.version} ({state.git_branch})\n"
                f"- System Health: {state.health.value.upper()}\n"
                f"- AI Host: {state.ai_host['status'].upper()}\n"
                f"- Database: {state.database['status'].upper()}\n"
                f"- Active Chips: {len(state.chips)}\n"
                f"- Uptime: {int(state.uptime_seconds // 3600)}h {int((state.uptime_seconds % 3600) // 60)}m\n"
                f"{healing_note}\n\n"
                f"Would you like to see the list of active chips or latest audit results?"
            )
        
        return AICommandResponse(
            intent="system_status",
            status="success",
            message=message,
            payload={"state": state.model_dump(mode='json')}
        )

    def _format_chips_response(self, state, lang: str) -> AICommandResponse:
        chip_list = "\n".join([f"- {c.name} ({c.slug}): {c.health.value} [{c.status}]" for c in state.chips])
        
        if lang == "es":
            message = (
                f"CHIPS DEL SISTEMA REGISTRADOS\n"
                f"Hay {len(state.chips)} chips activos en el ecosistema:\n\n"
                f"{chip_list}\n\n"
                f"Puedes pedirme que inspeccione cualquiera de ellos o que los abra en el shell."
            )
        else:
            message = (
                f"REGISTERED SYSTEM CHIPS\n"
                f"There are currently {len(state.chips)} active chips in the ecosystem:\n\n"
                f"{chip_list}\n\n"
                f"You can ask me to inspect any of these or open them in your shell."
            )
        
        return AICommandResponse(
            intent="list_chips",
            status="success",
            message=message,
            payload={"chips": [c.model_dump(mode='json') for c in state.chips]}
        )
