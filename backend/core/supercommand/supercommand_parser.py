import logging
from typing import Dict, Any, List, Optional
from .supercommand_models import SuperCommandIntent, TaskCategory

logger = logging.getLogger(__name__)

class SuperCommandParser:
    """Detects complex task intentions within natural language commands."""
    
    KEYWORD_MAP = {
        "optimize": TaskCategory.OPTIMIZATION,
        "improve": TaskCategory.OPTIMIZATION,
        "harden": TaskCategory.OPTIMIZATION,
        "teach": TaskCategory.LEARNING,
        "learn": TaskCategory.LEARNING,
        "describe": TaskCategory.LEARNING,
        "explain": TaskCategory.LEARNING,
        "explore": TaskCategory.EXPLORATION,
        "map": TaskCategory.EXPLORATION,
        "analyze": TaskCategory.ARCHITECTURE,
        "architecture": TaskCategory.ARCHITECTURE,
        "simulate": TaskCategory.SIMULATION,
        "build": TaskCategory.SIMULATION,
        "create simulation for": TaskCategory.SIMULATION
    }

    def parse(self, text: str) -> Optional[SuperCommandIntent]:
        """Tries to parse a natural command into a SuperCommandIntent."""
        text = text.lower().strip()
        
        # 1. Simple Keyword Matching
        matched_category = TaskCategory.GENERAL
        matched_keyword = None
        
        for k, category in self.KEYWORD_MAP.items():
            if k in text:
                # Prioritize longer keyword matches
                if matched_keyword is None or len(k) > len(matched_keyword):
                    matched_category = category
                    matched_keyword = k
        
        if matched_keyword:
            # Complexity is higher for certain categories
            complexity = 0.5
            if matched_category in [TaskCategory.OPTIMIZATION, TaskCategory.SIMULATION]:
                complexity = 0.8
            elif matched_category in [TaskCategory.LEARNING, TaskCategory.EXPLORATION]:
                complexity = 0.4
            
            # Extract target
            target = text.replace(matched_keyword, "").strip()
            
            return SuperCommandIntent(
                category=matched_category,
                command=text,
                target=target,
                complexity=complexity
            )
        
        return None

supercommand_parser = SuperCommandParser()
