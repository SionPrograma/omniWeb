import logging
from typing import Dict, Any, Optional
from backend.core.web_window_engine.web_window_controller import web_window_controller
from backend.core.multi_ai_interface.agent_manager import agent_manager
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class InterfaceProcessor(CommandProcessor):
    """Handles commands relating to the Multi-AI space and Web Windows."""
    
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg = msg.lower()
        
        # 1. Handle Window Opening
        if "abrir" in msg or "open" in msg:
            url = ""
            if "youtube" in msg: url = "https://www.youtube.com/embed"
            elif "google" in msg: url = "https://www.google.com/search?igu=1"
            elif "wikipedia" in msg: url = "https://en.wikipedia.org"
            
            if url:
                win = web_window_controller.create_window(url)
                return AICommandResponse(
                    intent="interface_window",
                    message=f"Abriendo ventana flotante para {win.title}.",
                    status="success",
                    payload={"window": win.model_dump()}
                )

        # 2. Handle Agent Invitation
        if "invitar" in msg or "invite" in msg:
            agent_type = "coder" if "coder" in msg or "programador" in msg else "researcher"
            agent = agent_manager.invite_agent(agent_type)
            if agent:
                return AICommandResponse(
                    intent="interface_agent",
                    message=f"He invitado a {agent.name} ({agent.role}) al espacio de trabajo.",
                    status="success",
                    payload={"agent": agent.model_dump()}
                )

        return AICommandResponse(
            intent="interface_general",
            message="No entiendo esa instrucción de interfaz. Prueba con 'abrir youtube' o 'invitar programador'.",
            status="partial"
        )

interface_processor = InterfaceProcessor()
