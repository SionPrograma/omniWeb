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
        state = await state_engine.get_state()
        
        # 1. Detail Chip Query
        if any(x in cmd for x in ["chips", "módulos", "modules"]):
            return self._format_chips_response(state)
        
        # 2. General Health / Status
        return self._format_general_status(state)

    def _format_general_status(self, state) -> AICommandResponse:
        health_icon = "✅"
        if state.health == SystemHealth.WARNING: health_icon = "⚠️"
        elif state.health == SystemHealth.ERROR: health_icon = "❌"
        
        healing_note = "\n\n✨ *The system is currently self-healing...*" if state.is_healing else ""
        
        message = (
            f"### {health_icon} Unified System Status\n"
            f"- **Version**: {state.version} (`{state.git_branch}`)\n"
            f"- **System Health**: {state.health.value.upper()}\n"
            f"- **AI Host**: {state.ai_host['status'].capitalize()}\n"
            f"- **Database**: {state.database['status'].capitalize()}\n"
            f"- **Active Chips**: {len(state.chips)}\n"
            f"- **Uptime**: {int(state.uptime_seconds // 3600)}h {int((state.uptime_seconds % 3600) // 60)}m\n"
            f"{healing_note}\n\n"
            f"Would you like to see the list of active chips or latest audit results?"
        )
        
        return AICommandResponse(
            intent="system_status",
            status="success",
            message=message,
            payload={"state": state.model_dump(mode='json')}
        )

    def _format_chips_response(self, state) -> AICommandResponse:
        chip_list = "\n".join([f"- **{c.name}** (`{c.slug}`): {c.health.value} ({c.status})" for c in state.chips])
        message = (
            f"### 🧩 Registered System Chips\n"
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
