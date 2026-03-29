import logging
import random
import re
from typing import Dict, Any, Optional, List
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse
from backend.core.ai_host.orchestration.executive_synthesis import executive_synthesis

logger = logging.getLogger(__name__)

class GeneralChatProcessor(CommandProcessor):
    """
    Handles unstructured conversation, greetings, status checks, 
    and general knowledge queries using memory-augmented synthesis.
    """
    
    CONTINUITY_KEYWORDS = [
        "haciendo", "que estábamos", "qué estábamos", "qué estabamos", "que estabamos",
        "andábamos", "andabamos", "qué veníamos", "que veniamos", "continuidad",
        "qué hicimos", "que hicimos", "recién", "lo último", "lo ultimo", "hicimos recién",
        "en qué estábamos", "en que estabamos", "retomemos", "anterior", "veníamos mirando", "veníamos analizando",
        "ajustar", "terminando", "tocar", "hilo", "veníamos haciendo"
    ]
    
    MEMORY_QUERY_KEYWORDS = [
        "vigente", "archivo", "módulo", "modulo", "bloque", "roadmap", "plan",
        "pendientes", "pendiente", "diferido", "pospuesto", "sensible", "riesgo",
        "closed", "already", "bugs", "done", "módulo", "modulo", "archivo", 
        "hicimos", "andábamos", "andabamos", "comprometido", "reabrir", "pertenece",
        "qué estamos cerrando", "qué veníamos cerrando", "qué cerramos"
    ]
    GREETINGS = ["hola", "hello", "hi", "hey", "buenos dias", "buenas tardes", "buenas noches", "buenos días", "todo bien", "todo ok", "buenas"]
    WHO_ARE_YOU = ["quien eres", "quién eres", "who are you", "que eres", "qué eres", "what are you", "tu nombre", "your name"]
    HOW_ARE_YOU = ["como estas", "cómo estás", "how are you", "que tal", "qué tal", "como vas", "cómo vas", "todo bien", "qué pasa", "que pasa"]
    ACKNOWLEDGMENTS = ["perfecto", "dale", "seguimos", "genial", "gracias", "ok", "listo", "entendido", "bien", "claro", "awesome", "great", "thanks", "got it", "understood"]

    async def can_handle(self, command: str) -> bool:
        """Always returns True as a universal fallback, but logic determines specificity."""
        return True

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        """Processes the command using semantic memory and executive synthesis."""
        msg = command.lower().strip()
        cmd = msg # Alias for shorter ref
        words = msg.split()
        lang = "es" # Default
        
        # 0. Context extraction
        if context:
            lang = context.get("language", "es")

        # 1. Memory Continuity & Project Scope (Primary Balance)
        # If the user asks what we were doing or details about the work
        if any(kw in cmd for kw in self.CONTINUITY_KEYWORDS) or \
           any(kw in cmd for kw in self.MEMORY_QUERY_KEYWORDS):
             
             # Use the global AI Host memory via the synthesis engine
             # Note: orchestration usually passes system_memory but if not, use default
             from backend.core.ai_host.memory.system_memory import system_memory
             w = system_memory.get_working()
             p = system_memory.get_project()
             
             # Centralized synthesize call (Unified across processors)
             tone = context.get("tone") if context else None
             msg_out = executive_synthesis.synthesize(w, p, msg, lang=lang, tone=tone)
             
             # Specific Intent logic for fixes list if specifically asked
             if ("fix" in cmd or "cerrado" in cmd) and len(cmd.split()) < 6:
                 return AICommandResponse(intent="project_status", status="success", message=msg_out)
             
             return AICommandResponse(intent="system_memory_report", status="success", message=msg_out)

        # 2. Greetings & Acknowledgments
        if any(w in words or w in cmd for w in self.GREETINGS):
            if lang == "es":
                responses = [
                    "¡Hola! ¿Todo bien por ahí? Decime en qué puedo ayudarte hoy.",
                    "¡Buenas! Acá reportándome. ¿Qué tenemos para hoy?",
                    "¡Hola! Listos para seguir. Vos dirás qué paso damos.",
                    "¡Buenas! ¿En qué andamos?"
                ]
            else:
                responses = [
                    "Hello! Everything okay there? Let me know how I can help today.",
                    "Hey! Reporting in. What's on the agenda?",
                    "Hi! Ready to go. You tell me what step we take.",
                    "Hello! What are we working on?"
                ]
            return AICommandResponse(intent="greeting", status="success", message=random.choice(responses))

        if any(w == words[0] if words else False for w in self.ACKNOWLEDGMENTS):
             if lang == "es":
                  msg_out = "¡Excelente! Seguimos entonces."
             else:
                  msg_out = "Excellent! Let's keep going then."
             return AICommandResponse(intent="acknowledgment", status="success", message=msg_out)

        # 3. Identity (Who am I?)
        if any(w in words or w in cmd for w in self.WHO_ARE_YOU):
            if lang == "es":
                msg_out = "Soy Omni, el núcleo de inteligencia de OmniWeb. Estoy aquí para ayudarte a construir, auditar y expandir tu ecosistema digital."
            else:
                msg_out = "I am Omni, the intelligence core of OmniWeb. I'm here to help you build, audit, and expand your digital ecosystem."
            return AICommandResponse(intent="identity", status="success", message=msg_out)

        # 4. Status/How are you
        if any(w in words or w in cmd for w in self.HOW_ARE_YOU):
            if lang == "es":
                responses = [
                    "¡Todo impecable! Los procesos están estables y el cerebro funcionando a pleno. ¿Y vos?",
                    "Por ahora todo en orden por acá. Me siento listo para cualquier reto técnico hoy.",
                    "Sistema al 100%. ¿Cómo va tu día? ¿En qué nos enfocamos ahora?"
                ]
            else:
                responses = [
                    "Everything is great! Processes are stable and the brain is running at full capacity. And you?",
                    "All good over here for now. Feeling ready for any technical challenge today.",
                    "System at 100%. How's your day going? What are we focusing on now?"
                ]
            return AICommandResponse(intent="status_check", status="success", message=random.choice(responses))

        # 5. Fallback conversational reply
        tone = context.get("tone") if context else None
        if tone == "natural_chatbot" or any(w in cmd for w in ["raro", "entiendes", "confuso", "weird", "wrong"]):
             if lang == "es":
                  msg_out = "Acá estoy, tal vez me puse un poco rígido repasando los módulos. ¿Todo bien por ahí? ¿Qué tenías en mente?"
             else:
                  msg_out = "I'm here, maybe I got a bit too rigid reviewing the modules. Everything okay? What's on your mind?"
        elif lang == "es":
            msg_out = f"No detecté un comando operativo específico, pero acá estoy. Si querés que hagamos un chequeo técnico, decime el chip o el incidente. Si no, ¡podemos seguir charlando!"
        else:
            msg_out = f"I didn't detect an operational command, but I'm here. Let me know if you want a technical check or just want to chat."
            
        return AICommandResponse(intent="general_chat", status="success", message=msg_out)
