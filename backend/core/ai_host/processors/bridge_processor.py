import logging
from typing import Dict, Any
from backend.core.language_bridge.conversation_bridge import conversation_bridge, LanguageCode, BridgeUserConfig
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class BridgeProcessor(CommandProcessor):
    """Bridges AI Host commands to the Real-Time Language Bridge system."""
    
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg = msg.lower()
        
        # 1. Start Session
        if "activar traduccion" in msg or "language bridge" in msg:
            # Set default config if missing
            if user_id not in conversation_bridge.user_configs:
                conversation_bridge.user_configs[user_id] = BridgeUserConfig(
                    user_id=user_id,
                    preferred_listening_language=LanguageCode.ENGLISH
                )
            
            return AICommandResponse(
                intent="bridge_start",
                message="Sistema de Puente Lingüístico activado. Listo para traducción en tiempo real.",
                status="success"
            )

        # 2. Change Language
        if "escuchar en" in msg or "listen in" in msg:
            # Simple parsing logic
            target = LanguageCode.ENGLISH
            if "árabe" in msg or "arabic" in msg: target = LanguageCode.ARABIC
            elif "español" in msg or "spanish" in msg: target = LanguageCode.SPANISH
            
            if user_id in conversation_bridge.user_configs:
                conversation_bridge.user_configs[user_id].preferred_listening_language = target
            
            return AICommandResponse(
                intent="bridge_config",
                message=f"Configuración actualizada: Ahora escucharás en {target.name}.",
                status="success"
            )

        # 3. Simulate Utterance (for testing/demo)
        if "simular habla" in msg:
            speaker = await conversation_bridge.register_speaker("User Alpha", LanguageCode.SPANISH)
            res = await conversation_bridge.process_utterance(speaker, "Hola, gracias", user_id)
            return AICommandResponse(
                intent="bridge_simulation",
                message=f"Traducción procesada: {res['translated_text']}",
                status="success",
                payload=res
            )

        return AICommandResponse(
            intent="bridge_general",
            message="Comando de Puente Lingüístico no reconocido. Prueba con 'activar traduccion' o 'escuchar en árabe'.",
            status="partial"
        )

bridge_processor = BridgeProcessor()
