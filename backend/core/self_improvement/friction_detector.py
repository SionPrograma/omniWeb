import logging
from typing import List, Dict, Any
from .pattern_analyzer import pattern_analyzer

logger = logging.getLogger(__name__)

class FrictionDetector:
    """
    Identifies inefficiences in system usage.
    """
    def detect_repeated_manual_switching(self) -> List[Dict[str, Any]]:
        """
        Looks for frequent, manual switching between specific chips.
        This signals a potential multi-chip workflow that could be optimized.
        """
        raw_patterns = pattern_analyzer.get_frequent_sequences(limit=100)
        frictions = []
        
        # Simple rule: if we see two chips being opened consecutively frequently
        # they might benefit from a combined workflow or more efficient switching.
        for p in raw_patterns:
            if p["type"] == "repeated_orchestration":
                frictions.append({
                    "cause": "frequent_app_switching",
                    "involved_chips": p["chips"],
                    "description": f"Se detectó un cambio recurrente entre {', '.join(p['chips'])}."
                })
        return frictions

    def detect_frequent_commands_without_workflow(self) -> List[Dict[str, Any]]:
        """
        Looks for common intents that don't have a dedicated workflow yet.
        """
        intents = pattern_analyzer.get_most_common_intents()
        frictions = []
        for i in intents:
            if i["count"] >= 3: # If user did this 3 times+
                frictions.append({
                    "cause": "lack_of_automation",
                    "intent": i["intent"],
                    "description": f"Has solicitado '{i['intent']}' frecuentemente. ¿Automatizamos esto?"
                })
        return frictions

friction_detector = FrictionDetector()
