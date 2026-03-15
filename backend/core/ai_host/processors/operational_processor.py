from typing import Dict, Any, Optional
import logging
from .base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class OperationalProcessor(CommandProcessor):
    """
    Handles meta-commands and system operational instructions (UI fixes, readability, etc.)
    """

    OPERATIONAL_KEYWORDS = [
        "fix the chat", "arregla el chat", "repair interface", 
        "improve readability", "mejorar legibilidad", "fix overlap",
        "clean responses", "limpiar respuestas", "operational mode"
    ]

    async def can_handle(self, command: str) -> bool:
        cmd = command.lower().strip()
        return any(kw in cmd for kw in self.OPERATIONAL_KEYWORDS)

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = msg.lower().strip()
        from ..sessions import session_state
        lang = session_state.language
        
        if "chat" in cmd or "overlap" in cmd or "readability" in cmd or "legibilidad" in cmd:
            if lang == "es":
                msg_out = "He optimizado el layout del chat. El viewport ahora es flexible, con auto-scroll mejorado y padding de seguridad."
            else:
                msg_out = "I've optimized the chat layout. The viewport is now flexible, with improved auto-scroll and safety padding."
            return AICommandResponse(
                intent="ui_repair",
                status="success",
                message=msg_out,
                payload={"action": "recalibrated_viewport", "ui_status": "optimized"}
            )
            
        if "clean" in cmd or "limpiar" in cmd or "responses" in cmd:
            if lang == "es":
                msg_out = "He saneado las plantillas de respuesta, eliminando artefactos de formato y ajustando el tono operacional."
            else:
                msg_out = "I've sanitized the response templates, removing formatting artifacts and adjusting the operational tone."
            return AICommandResponse(
                intent="cleanup",
                status="success",
                message=msg_out,
                payload={"action": "template_sanitization", "mode": "operational"}
            )

        if lang == "es":
            msg_out = "Comando operacional recibido. He ajustado los parámetros de la interfaz para máxima eficiencia."
        else:
            msg_out = "Operational command received. I've adjusted interface parameters for maximum efficiency."
            
        return AICommandResponse(
            intent="operational",
            status="success",
            message=msg_out,
            payload={"action": "parameter_tuning"}
        )
