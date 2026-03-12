import logging
from typing import Dict, Any, List
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse
from backend.core.knowledge_os.workspace_manager import workspace_manager, InteractionMode

logger = logging.getLogger(__name__)

class OSProcessor(CommandProcessor):
    """Handles kernel-level commands for the Knowledge OS."""
    
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg = msg.lower()
        
        # 1. Mode Switching
        if "entrar a modo espacial" in msg or "spatial mode" in msg:
            workspace_manager.switch_mode(InteractionMode.SPATIAL)
            return AICommandResponse(
                intent="os_mode_switch",
                message="Sistema OmniWeb v2.0: Transicionando a entorno espacial 360.",
                status="success",
                payload={"mode": "spatial"}
            )

        # 2. Workspace Status
        if "estado del sistema" in msg or "system status" in msg:
            return AICommandResponse(
                intent="os_status",
                message=f"OmniWeb Kernel v2.0 - Running. Tools: {len(workspace_manager.state.active_tools)}",
                status="success",
                payload={"state": workspace_manager.state.model_dump()}
            )

        # 3. Knowledge Economy Matching
        if "oportunidades" in msg or "opportunit" in msg:
            return AICommandResponse(
                intent="economy_query",
                message="Escaneando el mercado global de conocimiento para tu perfil...",
                status="success",
                payload={"redirect": "/api/v1/economy/matches"}
            )

        return AICommandResponse(
            intent="os_general",
            message="Comando de kernel no reconocido. Intenta 'estado del sistema' o 'modo espacial'.",
            status="partial"
        )

os_processor = OSProcessor()
