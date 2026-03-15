from typing import Optional
from .patterns import INTENT_PATTERNS, any_pattern_matches

class IntentClassifier:
    """
    Decoupled intent classifier using rule-based and pattern matching.
    """
    def __init__(self):
        # Mappings from patterns.py
        self.rules = INTENT_PATTERNS

    def classify(self, msg: str) -> Optional[str]:
        msg = msg.lower()
        
        # 1. High Priority Intent Chains (Hardcoded priority)
        # Order matters here: more specific patterns should be checked first
        
        # Memory / Creator Mode Intents (Highest Priority)
        memory_intents = [
            "idea_captured", "list_ideas", "search_knowledge", "list_clusters", 
            "show_cluster", "group_ideas", "summarize_cluster", "generate_project_draft",
            "initialize_project", "show_cluster_lineage", "show_project_evolution",
            "show_project_activity", "scan_projects", "generate_evolution_report",
            "get_project_timeline"
        ]
        
        for intent in memory_intents:
            if any_pattern_matches(msg, self.rules.get(intent, [])):
                return intent
                
        # 2. Platform Operations
        if any_pattern_matches(msg, self.rules.get("launch_pipeline", ["launch pipeline", "pipeline", "workflow"])):
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
            
        if any(w in msg for w in ["open", "abrir", "abre"]) and "chip" in msg:
            return "open_chip"

        # 3. Fallback to generic rule matching
        for intent, patterns in self.rules.items():
            if any_pattern_matches(msg, patterns):
                return intent
                    
        return None

intent_classifier = IntentClassifier()
