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

        # 1. Jokes / Fun (Silent Director: Prioridad absoluta para evitar falsos positivos)
        if any(w in cmd for w in ["chiste", "joke", "reite", "reí"]):
             if lang == "es":
                  chistes = [
                      "¿Qué le dice un bit a otro? ... Nos vemos en el bus.",
                      "A un programador le dicen: 'Andá al súper y traé una leche. Si hay huevos, traé seis'. El tipo volvió con seis leches.",
                      "¿Por qué los programadores confunden Halloween con Navidad? Porque Oct 31 == Dec 25."
                  ]
                  msg_joke = f"¡Ja! Ahí va uno: {random.choice(chistes)}"
             else:
                  jokes = [
                      "Why do programmers always mix up Christmas and Halloween? Because Oct 31 equals Dec 25.",
                      "A SQL query walks into a bar, walks up to two tables, and asks... 'Can I join you?'",
                      "How many programmers does it take to change a light bulb? None, that's a hardware problem."
                  ]
                  msg_joke = f"Haha! Here is one: {random.choice(jokes)}"
             return AICommandResponse(intent="joke", status="success", message=msg_joke)

        # 2. Memory Continuity & Project Scope (Primary Balance)
        if any(kw in cmd for kw in self.CONTINUITY_KEYWORDS) or \
           any(kw in cmd for kw in self.MEMORY_QUERY_KEYWORDS):
             
             from backend.core.ai_host.memory.system_memory import system_memory
             w = system_memory.get_working()
             p = system_memory.get_project()
             
             tone = context.get("tone") if context else None
             msg_out = executive_synthesis.synthesize(w, p, msg, lang=lang, tone=tone)
             
             if ("fix" in cmd or "cerrado" in cmd) and len(cmd.split()) < 6:
                 return AICommandResponse(intent="project_status", status="success", message=msg_out)
             
             return AICommandResponse(intent="system_memory_report", status="success", message=msg_out)

        # 3. Greetings & Acknowledgments
        if any(w in words or w in cmd for w in self.GREETINGS):
            if lang == "es":
                responses = [
                    "¡Hola! Todo bien por acá. ¿En qué puedo ayudarte?",
                    "¡Buenas! ¿Cómo va todo? Vos dirás por dónde seguimos.",
                    "¡Hola! Un gusto saludarte. ¿Qué tenemos en mente para hoy?",
                    "¡Buenas! Reportándome. ¿En qué andamos?"
                ]
            else:
                responses = [
                    "Hello! All good here. How can I help you?",
                    "Hey! How's it going? You tell me where we go next.",
                    "Hi! Great to see you. What's on your mind today?",
                    "Hello! Reporting in. What are we working on?"
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
                    "¡Todo impecable! Sistema estable y listo para la acción. ¿Y vos, cómo va eso?",
                    "Por ahora todo en orden por acá. Me siento con energía para cualquier reto técnico.",
                    "Sistema al 100%. ¿Cómo viene tu día? ¿En qué nos enfocamos ahora?",
                    "¡Muy bien! Procesando ideas y esperando tus órdenes. ¿Qué contás vos?"
                ]
            else:
                responses = [
                    "Everything is impeccable! System stable and ready for action. And you, how's it going?",
                    "All good over here for now. Feeling energetic for any technical challenge.",
                    "System at 100%. How's your day? What are we focusing on now?",
                    "Doing great! Processing ideas and waiting for your commands. What's up with you?"
                ]
            return AICommandResponse(intent="status_check", status="success", message=random.choice(responses))

        # 5. Jokes / Fun
        if any(w in cmd for w in ["chiste", "joke"]):
             if lang == "es":
                  chistes = [
                      "¿Qué le dice un bit a otro? ... Nos vemos en el bus.",
                      "A un programador le dicen: 'Andá al súper y traé una leche. Si hay huevos, traé seis'. El tipo volvió con seis leches.",
                      "¿Por qué los programadores confunden Halloween con Navidad? Porque Oct 31 == Dec 25."
                  ]
                  msg_out = f"¡Ja! Ahí va uno: {random.choice(chistes)}"
             else:
                  jokes = [
                      "Why do programmers always mix up Christmas and Halloween? Because Oct 31 equals Dec 25.",
                      "A SQL query walks into a bar, walks up to two tables, and asks... 'Can I join you?'",
                      "How many programmers does it take to change a light bulb? None, that's a hardware problem."
                  ]
                  msg_out = f"Haha! Here is one: {random.choice(jokes)}"
             return AICommandResponse(intent="joke", status="success", message=msg_out)

        # 6. Fallback conversational reply
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
