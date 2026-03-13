from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

class IntentClassifier:
    """
    Decoupled intent classifier using rule-based and pattern matching.
    Supports extensibility for Phase T: Universal Knowledge Command System.
    """
    def __init__(self):
        # Default core mappings
        self.rules: Dict[str, List[str]] = {
            "open_chip": ["open", "abrir", "launch", "ejecutar", "lanzar", "chip", "entrar a", "go to", "start", "inicia"],
            "log_entry": ["log", "guarda", "anota", "registra", "bug", "fix", "tarea", "task", "decision", "idea", "anótame", "registre", "notar", "apuntar"],
            "show_system_status": ["system state", "estado del sistema", "sistema", "how is the system", "salud", "status", "como va", "how's things", "system info", "información del sistema"],
            "show_logbook": ["show logbook", "show recent", "ver logbook", "muestrame", "historial", "bitacora", "roadmap", "que hay de nuevo", "recientes", "entradas", "logbook entries"],
            "launch_pipeline": ["launch pipeline", "launch workflow", "workflow", "pipeline", "desplegar", "deploy", "translation", "ejecutar flujo", "procesar"],
            "insights": ["insight", "mejorar", "optimizar", "sugerencia", "mejora", "análisis", "tips"],
            "modify": ["modificar", "modify", "parche", "patch", "edita", "cambia"],
            "memory": ["recordar", "memory", "historia", "continuar", "resume", "recall", "memoria"],
            "graph": ["explora", "explore", "relacion", "relates", "camino", "path", "grafo", "graph", "conexiones"],
            "antimodal": ["antimodal", "silencio", "silent", "compact", "fondo", "background", "distraccion", "distraction", "resumen", "summary"],
            "knowledge": ["explica", "explain", "entiende", "understand", "conecta", "connect", "mapa", "map", "aprende", "learn", "que es", "what is", "enseñame"],
            "healing": ["arregla", "cura", "sana", "fix system", "heal", "repara", "audita", "salud", "problemas", "audit"]
        }

    def classify(self, msg: str) -> Optional[str]:
        msg = msg.lower()
        
        # 1. High Priority / Specific Patterns
        if any(w in msg for w in ["launch pipeline", "launch workflow", "launch translation", "pipeline", "workflow"]):
            return "launch_pipeline"

        # Specialized check for logbook vs log entry
        if "logbook" in msg:
            if any(w in msg for w in ["show", "ver", "mues", "list", "get", "rec"]):
                return "show_logbook"
        
        if any(w in msg for w in ["log", "anota", "registra", "guarda", "anótame", "registre"]):
            if "logbook" not in msg or any(w in msg for w in ["logbook entry", "in the logbook", "en el logbook"]):
                return "log_entry"
        
        if ("show" in msg or "ver" in msg or "muestrame" in msg or "get" in msg) and \
           ("logbook" in msg or "recent" in msg or "historial" in msg or "roadmap" in msg or "entradas" in msg):
            return "show_logbook"

        if "system" in msg or "estado" in msg or "how is" in msg or "how's" in msg or "sistema" in msg:
            return "show_system_status"
            
        if any(w in msg for w in ["arregla", "cura", "sana", "fix system", "repara", "heal"]):
             return "healing"
            
        if "open" in msg or "abrir" in msg or "launch chip" in msg or "lanzar" in msg:
            return "open_chip"
        
        # 2. General Rules
        # Prioritize according to request importance
        priority_intents = ["launch_pipeline", "show_logbook", "show_system_status", "log_entry", "open_chip", "insights", "modify", "knowledge"]
        for intent in priority_intents:
            if intent in self.rules:
                if any(pattern in msg for pattern in self.rules[intent]):
                    return intent
                    
        return None

intent_classifier = IntentClassifier()
