import logging
from typing import Dict, Any
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class AccessibilityLayer:
    """
    Phase 36: Accessibility Interaction Layer.
    Ensures OmniWeb is usable by all humans.
    """
    async def get_profile(self, user_id: str) -> Dict[str, Any]:
        async with db_manager.get_session() as session:
            res = await session.execute("SELECT * FROM accessibility_profiles WHERE user_id = :uid", {"uid": user_id})
            row = res.fetchone()
            if row:
                return dict(row)
            return {
                "voice_navigation": False,
                "braille_mode": False,
                "cognitive_level": 0
            }

    async def update_profile(self, user_id: str, data: Dict[str, Any]):
        query = """
        INSERT INTO accessibility_profiles (user_id, voice_navigation_enabled, braille_output_mode, cognitive_simplification_level)
        VALUES (:uid, :voice, :braille, :lvl)
        ON CONFLICT (user_id) DO UPDATE SET
            voice_navigation_enabled = EXCLUDED.voice_navigation_enabled,
            braille_output_mode = EXCLUDED.braille_output_mode,
            cognitive_simplification_level = EXCLUDED.cognitive_simplification_level
        """
        async with db_manager.get_session() as session:
            await session.execute(query, {
                "uid": user_id, 
                "voice": data.get("voice", False),
                "braille": data.get("braille", False),
                "lvl": data.get("level", 0)
            })
            await session.commit()
        logger.info(f"AccessibilityLayer: Profile updated for {user_id}")

accessibility_layer = AccessibilityLayer()
