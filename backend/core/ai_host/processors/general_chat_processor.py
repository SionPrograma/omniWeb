from typing import Dict, Any, Optional
import logging
import random
from .base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class GeneralChatProcessor(CommandProcessor):
    """
    Handles general conversation and provides a more 'human-like' fallback 
    than just saving to the Idea Cloud.
    """

    GREETINGS = ["hola", "hello", "hi", "hey", "buenos dias", "buenas tardes", "buenas noches", "buenos días"]
    WHO_ARE_YOU = ["quien eres", "quién eres", "who are you", "que eres", "qué eres", "what are you", "tu nombre", "your name"]
    HOW_ARE_YOU = ["como estas", "cómo estás", "how are you", "que tal", "qué tal", "como vas", "cómo vas"]

    async def can_handle(self, command: str) -> bool:
        cmd = command.lower().strip()
        words = cmd.split()
        
        # Detect language change triggers
        if any(k in cmd for k in ["responde en", "habla en", "idioma", "language", "speak in", "respond in"]):
            return True
        
        # Whole word matching for greetings or identity questions
        all_keywords = self.GREETINGS + self.WHO_ARE_YOU + self.HOW_ARE_YOU
        if any(w in words for w in all_keywords):
            return True
            
        # Also check for exact multi-word matches (like "who are you")
        if any(phrase in cmd for phrase in self.WHO_ARE_YOU + self.HOW_ARE_YOU if " " in phrase):
            return True

        # Extremely short messages (1 word) that aren't obviously commands
        if len(words) == 1 and cmd not in ["diagnostic", "diagnóstico", "log", "audit"]:
            return True
        return False

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = msg.lower().strip()
        from ..sessions import session_state
        
        # Detect language change (already partly handled in CreatorControl, but good to have here too)
        if any(k in cmd for k in ["responde en", "habla en", "idioma", "language", "speak in", "respond in"]):
            session_state.set_language(cmd)
        
        lang = session_state.language

        # 1. Greetings
        words = cmd.split()
        if any(w in words for w in self.GREETINGS):
            if lang == "es":
                responses = [
                    "¡Hola! Soy Omni, tu asistente de creación. ¿En qué puedo ayudarte hoy?",
                    "Hola. El sistema está listo para tus comandos. ¿Qué tienes en mente?",
                    "¡Hola! Estoy monitoreando tus chips y memoria. ¿Quieres empezar algo nuevo?"
                ]
            else:
                responses = [
                    "Hello! I am Omni, your creation assistant. How can I help you today?",
                    "Hi there. The system is ready for your commands. What's on your mind?",
                    "Hello! I'm monitoring your chips and memory. Want to start something new?"
                ]
            return AICommandResponse(intent="greeting", status="success", message=random.choice(responses))

        # 2. Identity
        if any(w in words or w in cmd for w in self.WHO_ARE_YOU):
            if lang == "es":
                msg_out = "Soy Omni, el núcleo de inteligencia de OmniWeb. Estoy aquí para ayudarte a construir, auditar y expandir tu ecosistema digital."
            else:
                msg_out = "I am Omni, the intelligence core of OmniWeb. I'm here to help you build, audit, and expand your digital ecosystem."
            return AICommandResponse(intent="identity", status="success", message=msg_out)

        # 3. Status/How are you
        if any(w in words or w in cmd for w in self.HOW_ARE_YOU):
            if lang == "es":
                msg_out = "Sistema operando al 100%. Todos los procesos están estables y los chips sincronizados. ¿En qué trabajamos hoy?"
            else:
                msg_out = "System operating at 100%. All processes are stable and chips are synchronized. What are we working on today?"
            return AICommandResponse(intent="status_check", status="success", message=msg_out)

        # 4. Fallback conversational reply
        if lang == "es":
            res_msg = f"He anotado tu mensaje en la Nube de Ideas ('{msg[:40]}...'). No detecté un comando específico, pero estoy listo para cualquier instrucción operacional."
        else:
            res_msg = f"I've saved your message to the Idea Cloud ('{msg[:40]}...'). I didn't detect a specific command, but I'm ready for any operational instructions."
            
        return AICommandResponse(intent="general_chat", status="success", message=res_msg)
