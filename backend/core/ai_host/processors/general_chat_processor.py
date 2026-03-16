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
    ACKNOWLEDGMENTS = ["perfecto", "dale", "seguimos", "genial", "gracias", "ok", "listo", "entendido", "bien", "claro", "awesome", "great", "thanks", "got it", "understood"]

    async def can_handle(self, command: str) -> bool:
        cmd = command.lower().strip()
        words = cmd.split()
        
        # Detect language change triggers
        if any(k in cmd for k in ["responde en", "habla en", "idioma", "language", "speak in", "respond in"]):
            return True
        
        # Whole word matching for greetings, identity, or acknowledgments
        all_keywords = self.GREETINGS + self.WHO_ARE_YOU + self.HOW_ARE_YOU + self.ACKNOWLEDGMENTS
        if any(w in words for w in all_keywords):
            return True
            
        # Also check for exact multi-word matches (like "who are you")
        if any(phrase in cmd for phrase in self.WHO_ARE_YOU + self.HOW_ARE_YOU if " " in phrase):
            return True

        # Extremely short messages (1 word) that aren't obviously commands
        if len(words) == 1 and cmd not in ["diagnostic", "diagnóstico", "log", "audit", "memory", "memoria"]:
            return True
        return False

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = msg.lower().strip()
        from ..sessions import session_state
        
        # Detect language change
        if any(k in cmd for k in ["responde en", "habla en", "idioma", "language", "speak in", "respond in"]):
            session_state.set_language(cmd)
        
        lang = session_state.language
        words = cmd.split()

        # 1. Greetings
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

        # 2. Acknowledgments
        if any(w in words for w in self.ACKNOWLEDGMENTS):
            if lang == "es":
                responses = [
                    "¡Excelente! Seguimos adelante.",
                    "Entendido. Estoy a la espera de tu próxima instrucción.",
                    "Genial, cuéntame más o dime qué chip quieres abrir ahora.",
                    "Perfecto. El sistema se mantiene estable."
                ]
            else:
                responses = [
                    "Excellent! Let's keep going.",
                    "Understood. Awaiting your next instruction.",
                    "Great, tell me more or let me know which chip you'd like to open next.",
                    "Perfect. System remains stable."
                ]
            return AICommandResponse(intent="acknowledgment", status="success", message=random.choice(responses))

        # 3. Identity
        if any(w in words or w in cmd for w in self.WHO_ARE_YOU):
            if lang == "es":
                msg_out = "Soy Omni, el núcleo de inteligencia de OmniWeb. Estoy aquí para ayudarte a construir, auditar y expandir tu ecosistema digital."
            else:
                msg_out = "I am Omni, the intelligence core of OmniWeb. I'm here to help you build, audit, and expand your digital ecosystem."
            return AICommandResponse(intent="identity", status="success", message=msg_out)

        # 4. Status/How are you
        if any(w in words or w in cmd for w in self.HOW_ARE_YOU):
            if lang == "es":
                msg_out = "Sistema operando al 100%. Todos los procesos están estables y los chips sincronizados. ¿En qué trabajamos hoy?"
            else:
                msg_out = "System operating at 100%. All processes are stable and chips are synchronized. What are we working on today?"
            return AICommandResponse(intent="status_check", status="success", message=msg_out)

        # 5. Fallback conversational reply
        if lang == "es":
            res_msg = f"No detecté un comando operativo específico para '{msg[:40]}...'. Si quieres guardar una idea, prueba con 'guarda esta idea:'. De lo contrario, ¿qué chip te gustaría inspeccionar?"
        else:
            res_msg = f"I didn't detect a specific operational command for '{msg[:40]}...'. If you want to save an idea, try 'save this idea:'. Otherwise, which chip would you like to inspect?"
            
        return AICommandResponse(intent="general_chat", status="success", message=res_msg)
