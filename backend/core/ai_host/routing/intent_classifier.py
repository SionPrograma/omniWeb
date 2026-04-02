import re
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
        priority_intents = [
            "copilot_proposal", "mission_followup", "mission_approve", "mission_cancel", "mission_status",
            "memory_continuity", "memory_project",
            "idea_captured", "list_ideas", "search_knowledge", "list_clusters", 
            "show_cluster", "group_ideas", "summarize_cluster", "generate_project_draft",
            "initialize_project", "show_cluster_lineage", "show_project_evolution",
            "show_project_activity", "scan_projects", "generate_evolution_report",
            "get_project_timeline"
        ]
        
        for intent in priority_intents:
            if any_pattern_matches(msg, self.rules.get(intent, [])):
                return intent
                
        # 2. Platform Operations
        
        # Specialized check for logbook vs log entry - Use whole word matching
        if re.search(r"\blogbook\b", msg):
            if any(re.search(rf"\b{w}\b", msg) for w in ["show", "ver", "mues", "list", "get", "rec"]):
                return "show_logbook"
        
        # Log Entry Trigger - Tightened to explicit keywords at start or as pure commands
        log_triggers = ["log", "anota", "registra", "guarda", "anótame", "registre"]
        if any(re.search(rf"\b{w}\b", msg) for w in log_triggers):
             # Only if it's not a generic conversation like "guarda silencio" (though unusual)
             # and specifically check for memory context if possible
             if any(re.search(rf"\b{w}\b", msg) for w in ["log", "logbook", "memoria", "idea", "pensamiento", "nota"]):
                 return "log_entry"
        
        if any(re.search(rf"\b{w}\b", msg) for w in ["show", "ver", "muestrame", "get"]):
             if any(re.search(rf"\b{w}\b", msg) for w in ["logbook", "recent", "historial", "roadmap", "entradas"]):
                 return "show_logbook"

        # Creator Analysis & Planning (Brain Layer)
        if any(re.search(rf"\b{w}\b", msg) for w in ["analiza", "analyze", "problema", "problem", "bottleneck", "cuello de botella"]):
             return "creator_analysis"
             
        if any(re.search(rf"\b{w}\b", msg) for w in ["plan", "paso a paso", "mejora", "improve", "propón", "propose", "sugiere", "suggest"]):
             return "creator_plan"

        if any(re.search(rf"\b{w}\b", msg) for w in ["system", "estado", "sistema", "saludable", "warning", "crítico", "nominales", "nominal", "evidencia", "real", "falla", "fallando", "fallo", "error"]) or "how is" in msg or "how's" in msg:
             if any(re.search(rf"\b{w}\b", msg) for w in ["audit", "audita", "auditá", "falla", "fallando", "diagnóstico", "diagnostico", "inspect", "revisa", "revisá", "qué pasa", "cómo está", "estás", "respondé", "responde", "qué está"]):
                 return "system_audit"
             return "show_system_status"
            
        if any(re.search(rf"\b{w}\b", msg) for w in ["arregla", "cura", "sana", "fix", "repara", "heal", "soluciona", "solve"]):
             return "healing"

        if any(re.search(rf"\b{w}\b", msg) for w in ["qué está mal", "what is wrong", "qué pasa", "what's wrong", "problemas", "anomalía", "anomaly"]):
             return "remediation"
            
        if any(re.search(rf"\b{w}\b", msg) for w in ["open", "abrir", "abre"]) and re.search(r"\bchip\b", msg):
            return "open_chip"

        # Acknowledgment Intent (New Stage 5)
        ack_words = ["perfecto", "dale", "seguimos", "genial", "gracias", "ok", "listo", "entendido", "claro"]
        if any(re.search(rf"^{w}\b", msg) for w in ack_words) or (len(msg.split()) == 1 and msg.strip(",.!") in ack_words):
             return "acknowledgment"

        # 3. Fallback to generic rule matching
        for intent, patterns in self.rules.items():
            if any_pattern_matches(msg, patterns):
                return intent
                    
        return None

intent_classifier = IntentClassifier()
