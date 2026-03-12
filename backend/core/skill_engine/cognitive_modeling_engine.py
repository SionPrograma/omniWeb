from typing import Dict, List
from datetime import datetime
from .skill_models import CognitiveMetric, SkillProfile
from .skill_profile_builder import skill_profile_builder

class CognitiveModelingEngine:
    def analyze_interactions(self, user_id: str, history: List[dict]):
        """
        Deeply analyzes user interactions to refine the cognitive profile.
        Detects patterns like 'systems_thinking', 'algorithmic_logic', 'linguistic_fluidity'.
        """
        profile = skill_profile_builder.get_profile(user_id)
        
        # Simulated cognitive pattern detection
        # In a real system, this would use NLP or behavioral analysis
        
        patterns = {
            "systems_thinking": 0.0,
            "creative_abstraction": 0.0,
            "empirical_deduction": 0.0
        }
        
        for interaction in history:
            text = str(interaction.get("text", "")).lower()
            if any(w in text for w in ["distribuido", "red", "nodos", "sistema"]):
                patterns["systems_thinking"] += 0.1
            if any(w in text for w in ["idea", "sueño", "posibilidad", "imagina"]):
                patterns["creative_abstraction"] += 0.1
            if any(w in text for w in ["prueba", "evidencia", "resultado", "dato"]):
                patterns["empirical_deduction"] += 0.1
                
        # Update metrics
        for name, score in patterns.items():
            current = profile.cognitive_metrics.get(name, CognitiveMetric(name=name, score=0.0, confidence=0.0))
            # Smooth update
            current.score = min(1.0, current.score + score)
            current.confidence = min(1.0, current.confidence + 0.05)
            current.last_detected = datetime.now()
            profile.cognitive_metrics[name] = current
            
        profile.last_analysis = datetime.now()
        # Here we would save the profile if persistent storage was active
        return profile

cognitive_modeling_engine = CognitiveModelingEngine()
