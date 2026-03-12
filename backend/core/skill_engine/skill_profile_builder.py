import logging
import json
from typing import Optional, List
from .skill_models import SkillProfile, CognitiveMetric
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class SkillProfileBuilder:
    """Aggregates metrics and mastery to build a unified skill profile."""
    
    def get_profile(self, user_id: str) -> SkillProfile:
        with set_chip_context("core"):
            metrics = self._get_metrics(user_id)
            mastery = self._get_top_mastery(user_id)
            
            # Simple aggregation
            profile = SkillProfile(
                user_id=user_id,
                cognitive_metrics={m.name: m for m in metrics},
                top_skills=mastery,
                learning_speed=metrics[0].score if metrics else 0.5
            )
            return profile

    def _get_metrics(self, user_id: str) -> List[CognitiveMetric]:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM cognitive_metrics WHERE user_id = ?", (user_id,)).fetchall()
            return [CognitiveMetric(
                name=row["metric_name"],
                score=row["score"],
                confidence=row["confidence"],
                last_detected=row["last_detected"]
            ) for row in rows]

    def _get_top_mastery(self, user_id: str) -> List[str]:
        # Connect with Education Engine (user_skills table)
        with db_manager.get_connection() as conn:
            rows = conn.execute(
                "SELECT concept FROM user_skills WHERE level > 0.7 ORDER BY level DESC LIMIT 5"
            ).fetchall()
            return [row["concept"] for row in rows]

skill_profile_builder = SkillProfileBuilder()
