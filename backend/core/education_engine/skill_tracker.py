import logging
import json
from typing import List, Dict, Any, Optional
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .education_models import UserSkill

logger = logging.getLogger(__name__)

class SkillTracker:
    """Tracks and persists user competency across various concepts."""
    
    def update_skill(self, concept: str, increment_xp: int = 10, level_boost: float = 0.05):
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT * FROM user_skills WHERE concept = ?", (concept,)).fetchone()
                if row:
                    new_xp = row["experience_points"] + increment_xp
                    new_level = min(1.0, row["level"] + level_boost)
                    conn.execute(
                        "UPDATE user_skills SET level = ?, experience_points = ?, last_updated = CURRENT_TIMESTAMP WHERE concept = ?",
                        (new_level, new_xp, concept)
                    )
                else:
                    conn.execute(
                        "INSERT INTO user_skills (concept, level, experience_points) VALUES (?, ?, ?)",
                        (concept, min(1.0, level_boost), increment_xp)
                    )
                conn.commit()

    def get_user_profile(self) -> List[UserSkill]:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM user_skills ORDER BY level DESC").fetchall()
                return [UserSkill(**dict(row)) for row in rows]

skill_tracker = SkillTracker()
