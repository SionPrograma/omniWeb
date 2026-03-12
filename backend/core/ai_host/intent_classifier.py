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
            "open": ["abrir", "open"],
            "create": ["crea", "create"],
            "activate": ["activa", "activate"],
            "deactivate": ["desactiva", "deactivate"],
            "status": ["estado", "status", "salud"],
            "list": ["listar", "list", "chips"],
            "suggest": ["preparar", "sugiere", "sesión"],
            "insights": ["insight", "mejorar", "optimizar", "sugerencia", "mejora"],
            "workflow": ["workflow", "flujo"],
            "modify": ["modificar", "modify", "parche"],
            "memory": ["recordar", "memory", "historia", "continuar", "resume", "recall"],
            "graph": ["explora", "explore", "relacion", "relates", "camino", "path", "grafo", "graph"],
            "antimodal": ["antimodal", "silencio", "silent", "compact", "fondo", "background", "distraccion", "distraction", "resumen", "summary"],
            "knowledge": ["explica", "explain", "entiende", "understand", "conecta", "connect", "mapa", "map", "aprende", "learn", "que es", "what is"]
        }

    def classify(self, msg: str) -> Optional[str]:
        msg = msg.lower()
        for intent, patterns in self.rules.items():
            if any(pattern in msg for pattern in patterns):
                return intent
        return None

intent_classifier = IntentClassifier()
