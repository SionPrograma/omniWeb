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
    HOW_ARE_YOU = [r"\bcomo estas\b", r"\bcómo estás\b", r"\bhow are you\b", r"\bque tal\b", r"\bqué tal\b", r"\bcomo vas\b", r"\bcómo vas\b", r"\btodo bien\b", r"\bqué pasa\b", r"\bque pasa\b"]
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
        
        if context:
            lang = context.get("language", "es")

        # 0.5 DIRECT HONESTY CHECK (Priority 0)
        # Category A & B (No entendí & No lo sé) detected by synthesis
        honest_msg = executive_synthesis.synthesize_conversational(cmd, lang=lang, context=context)
        # Check if the synthesis returned an honest fallback (No entendí / No lo sé)
        honest_markers = ["no lo sé", "no tengo idea", "no tengo cómo verificar", "confirmar", "mataste", "perdí", "perdido", "don't know", "lost", "don't have way to confirm"]
        if any(h in honest_msg.lower() for h in honest_markers):
             return AICommandResponse(intent="honest_fallback", status="success", message=honest_msg)

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
        is_pure_greeting = any(w == cmd for w in self.GREETINGS) or \
                          (len(words) <= 3 and any(w in words for w in self.GREETINGS) and not any(t in cmd for t in ["chip", "log", "módulo", "error", "falla", "build", "ayuda"]))
        
        if is_pure_greeting:
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
             msg_out = executive_synthesis.synthesize_conversational(cmd, lang=lang, context=context)
             return AICommandResponse(intent="identity", status="success", message=msg_out)

        # 4. Status/How are you
        if any(re.search(w, cmd) for w in self.HOW_ARE_YOU):
            if lang == "es":
                responses = [
                    "¡Todo impecable! Sistema estable y listo para la acción. ¿Y vos, cómo va eso?",
                    "Por ahora todo en orden por acá. Me siento con energía para cualquier reto técnico.",
                    "Sistema al 100%. ¿Cómo viene tu día? ¿En qué nos enfocamos ahora?",
                    "¡Muy bien! Procesando ideas y esperando tus órdenes. ¿Qué contás vos?",
                    "Mejor que nunca. La arquitectura está sólida y yo estoy listo. ¿Qué andamos planeando?" # New
                ]
            else:
                responses = [
                    "Everything is impeccable! System stable and ready for action. And you, how's it going?",
                    "All good over here for now. Feeling energetic for any technical challenge.",
                    "System at 100%. How's your day? What are we focusing on now?",
                    "Doing great! Processing ideas and waiting for your commands. What's up with you?"
                ]
            return AICommandResponse(intent="status_check", status="success", message=random.choice(responses))

        # 5. Fallback conversational reply
        msg_out = executive_synthesis.synthesize_conversational(cmd, lang=lang, context=context)
        return AICommandResponse(intent="general_chat", status="success", message=msg_out)
