import logging
import re
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class HumanInputInterpreter:
    """
    Interpretation Layer for messy/informal human input.
    Extracts intent, context, signals, and emotional state before cognitive processing.
    """
    
    def interpret(self, text: str) -> Dict[str, Any]:
        msg = text.lower().strip()
        
        interpretation = {
            "intent": self._extract_intent(msg),
            "context": self._extract_context(msg),
            "signals": self._extract_signals(msg),
            "clarity": self._assess_clarity(msg),
            "user_state": self._detect_user_state(msg),
            "original_text": text
        }
        
        logger.info(f"[HUMAN_INTERPRETATION] {interpretation}")
        return interpretation

    def _extract_intent(self, msg: str) -> str:
        # Debug/Fix triggers
        if any(w in msg for w in ["anda", "falla", "raro", "mal", "funciona", "arregla", "bug", "error"]):
            return "debug"
        # Creation triggers
        if any(w in msg for w in ["crea", "hace", "build", "pon", "agregá", "implementa"]):
            return "create"
        # Decision triggers
        if any(w in msg for w in ["decidi", "elegí", "cuál", "prioriza", "qué hago"]):
            return "decide"
        # Exploration/Question
        if any(w in msg for w in ["qué onda", "fijate", "mirá", "qué es"]):
            return "explore"
        
        return "neutral_query"

    def _extract_context(self, msg: str) -> str:
        if any(w in msg for w in ["chat", "habla", "responde", "dijo"]):
            return "conversational_behavior"
        if any(w in msg for w in ["ui", "visual", "pantalla", "botón", "color"]):
            return "interface_design"
        if any(w in msg for w in ["núcleo", "backend", "procesamiento", "lento", "cpu"]):
            return "core_system"
        if any(w in msg for w in ["memoria", "recordas", "dije antes"]):
            return "session_persistence"
        
        return "general_system"

    def _extract_signals(self, msg: str) -> List[str]:
        # Extract meaningful nouns or concepts
        signals = []
        key_terms = [
            "chat", "tono", "bug", "mobile", "interfaz", "log", "latency", "tarda",
            "lento", "latencia", "video", "responde", "vínculo", "link",
            "velocidad", "natural", "robot", "creador", "omni", "estilo",
            "ux", "ui", "arquitectura", "backend", "frontend", "lógica", "logic",
            "base", "núcleo", "core", "estado", "state", "buffer", "memoria",
            "mem", "cpu", "performance", "rendimiento", "estabilidad"
        ]
        for term in key_terms:
            if term in msg:
                signals.append(term)
        return signals

    def _assess_clarity(self, msg: str) -> str:
        words = msg.split()
        if len(words) < 4:
            return "ambiguous"
        if any(w in msg for w in ["algo", "onda", "medio", "tipo", "coso"]):
            return "partial"
        return "clear"

    def _detect_user_state(self, msg: str) -> str:
        if any(w in msg for w in ["mierda", "malísimo", "no anda", "harto", "che", "anda mal"]):
            return "frustrated"
        if any(w in msg for w in ["cómo", "por qué", "qué es esto", "perdido", "qué pasa", "no sé", "no se", "distinto"]):
            return "confused"
        if any(w in msg for w in ["mirá", "probá", "chequeá", "dale", "fijate"]):
            return "exploratory"
        return "neutral"

human_interpreter = HumanInputInterpreter()
