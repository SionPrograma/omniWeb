import logging
from typing import Dict, Any
from backend.core.global_communication.session_manager import session_manager, Participant, LanguageCode
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class CommunicationProcessor(CommandProcessor):
    """Bridges AI Host commands to the Global Communication Layer."""
    
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg = msg.lower()
        
        # 1. Dashboard Call / Session Creation
        if "iniciar llamada" in msg or "start call" in msg:
            creator = Participant(
                user_id=user_id, 
                name="User Alpha", 
                native_language=LanguageCode.SPANISH,
                listening_language=LanguageCode.SPANISH
            )
            session = session_manager.create_session("Conversación Global", creator)
            
            return AICommandResponse(
                intent="comm_session_start",
                message=f"Llamada iniciada. ID de sesión: {session.id}. Esperando participantes.",
                status="success",
                payload={"session_id": session.id}
            )

        # 2. Status check
        if "quién está" in msg or "who is in" in msg:
            active = session_manager.get_active_sessions()
            if not active:
                return AICommandResponse(intent="comm_status", message="No hay sesiones de comunicación activas.", status="success")
            
            p_names = [p.name for s in active for p in s.participants.values()]
            return AICommandResponse(
                intent="comm_status",
                message=f"Participantes activos en la red: {', '.join(p_names)}",
                status="success"
            )

        return AICommandResponse(
            intent="comm_general",
            message="Comando de comunicación no reconocido. Prueba con 'iniciar llamada'.",
            status="partial"
        )

comm_processor = CommunicationProcessor()
