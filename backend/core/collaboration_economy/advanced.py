import logging
import uuid
import json
from typing import Dict, Any, List
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class MentorManager:
    """Phase 43: Personal AI Mentor."""
    async def get_mentor_state(self, user_id: str) -> Dict[str, Any]:
        async with db_manager.get_session() as session:
            res = await session.execute("SELECT * FROM ai_mentor_profiles WHERE user_id = :uid", {"uid": user_id})
            row = res.fetchone()
            if not row:
                return {
                    "learning_style": "interactive",
                    "focus_areas": ["Distributed Systems", "AI Safety"],
                    "suggestions": ["Review Phase 30 Knowledge units", "Optimize Storage Grid nodes"]
                }
            return dict(row)

class OmniverseManager:
    """Phase 44: Omniverse Gateway."""
    async def get_user_gateways(self, user_id: str) -> List[Dict[str, Any]]:
        async with db_manager.get_session() as session:
            res = await session.execute("SELECT * FROM omniverse_gateways WHERE user_id = :uid", {"uid": user_id})
            return [dict(r) for r in res]

    async def create_gateway(self, user_id: str, title: str, coords: Dict[str, float]):
        gateway_id = str(uuid.uuid4())
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO omniverse_gateways (gateway_id, user_id, title, spatial_coordinates)
                VALUES (:gid, :uid, :title, :coords)
            """, {"gid": gateway_id, "uid": user_id, "title": title, "coords": json.dumps(coords)})
            await session.commit()
        return gateway_id

mentor_manager = MentorManager()
omniverse_manager = OmniverseManager()
