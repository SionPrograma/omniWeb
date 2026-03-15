import logging
import json
from typing import List, Dict, Any
from .skill_models import CognitiveMetric
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class SkillDetector:
    """Analyzes interaction patterns to detect cognitive metrics and skills."""
    
    async def detect_from_input(self, user_id: str, text: str, context: str = "general"):
        """Extracts hints of cognitive ability from raw text or command input."""
        with set_chip_context("core"):
            # Sample logic: Length and word complexity implies high technical communication
            words = text.split()
            complexity = len([w for w in words if len(w) > 7]) / (len(words) + 1)
            
            if complexity > 0.2:
                await self._update_metric(user_id, "communication", 0.1 * complexity)
            
            # Key technical terms logic (simplified)
            tech_terms = ["engine", "system", "architecture", "logical", "optimize"]
            tech_hits = sum(1 for t in tech_terms if t in text.lower())
            if tech_hits > 0:
                await self._update_metric(user_id, "systems_thinking", 0.05 * tech_hits)

    async def detect_from_exercise(self, user_id: str, score: float, topic: str):
        """Analyzes performance in educational exercises."""
        with set_chip_context("core"):
            if score > 0.8:
                await self._update_metric(user_id, "logical_reasoning", 0.05)
                await self._update_metric(user_id, "learning_speed", 0.02)
            elif score < 0.3:
                await self._update_metric(user_id, "logical_reasoning", -0.01)

    async def _update_metric(self, user_id: str, name: str, delta: float):
        from backend.core.integration_layer.event_bus import integration_bus
        
        with db_manager.get_connection() as conn:
            row = conn.execute(
                "SELECT score, confidence FROM cognitive_metrics WHERE user_id = ? AND metric_name = ?",
                (user_id, name)
            ).fetchone()
            
            new_score = 0.0
            if row:
                new_score = max(0.0, min(1.0, row["score"] + delta))
                new_conf = min(1.0, row["confidence"] + 0.05)
                conn.execute(
                    "UPDATE cognitive_metrics SET score = ?, confidence = ?, last_detected = CURRENT_TIMESTAMP WHERE user_id = ? AND metric_name = ?",
                    (new_score, new_conf, user_id, name)
                )
            else:
                new_score = max(0.0, min(1.0, delta * 2))
                conn.execute(
                    "INSERT INTO cognitive_metrics (user_id, metric_name, score, confidence) VALUES (?, ?, ?, ?)",
                    (user_id, name, new_score, 0.1)
                )
            conn.commit()
            
            # Emit integration event
            await integration_bus.emit_domain_event(
                "skill_detected",
                {"user_id": user_id, "metric_name": name, "score": new_score, "delta": delta},
                "skill_engine"
            )
            
            # Check threshold
            if new_score >= 0.7:
                 await integration_bus.emit_domain_event(
                    "skill_threshold_reached",
                    {"user_id": user_id, "skill_name": name, "score": new_score},
                    "skill_engine"
                )

skill_detector = SkillDetector()
