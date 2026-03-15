import logging
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class ReputationManager:
    """Phase 37: Reputation Engine."""
    async def get_reputation(self, user_id: str) -> Dict[str, Any]:
        async with db_manager.get_session() as session:
            res = await session.execute("SELECT * FROM reputation_profiles WHERE user_id = :uid", {"uid": user_id})
            row = res.fetchone()
            if not row:
                return {"user_id": user_id, "score": 100.0, "level": "Novice"}
            return dict(row)

    async def update_score(self, user_id: str, delta: float, reason: str):
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO reputation_profiles (user_id, score, contribution_count)
                VALUES (:uid, :score, 1)
                ON CONFLICT (user_id) DO UPDATE SET
                    score = reputation_profiles.score + :delta,
                    contribution_count = reputation_profiles.contribution_count + 1
            """, {"uid": user_id, "score": 100.0 + delta, "delta": delta})
            
            await session.execute("""
                INSERT INTO reputation_history (history_id, user_id, change_amount, reason)
                VALUES (:hid, :uid, :delta, :reason)
            """, {"hid": str(uuid.uuid4()), "uid": user_id, "delta": delta, "reason": reason})
            await session.commit()

class CollabManager:
    """Phase 38: Project Collaboration Engine."""
    async def create_project(self, creator_id: str, title: str, description: str) -> str:
        project_id = str(uuid.uuid4())
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO collaborative_projects (project_id, creator_id, title, description, status)
                VALUES (:pid, :cid, :title, :desc, 'active')
            """, {"pid": project_id, "cid": creator_id, "title": title, "desc": description})
            
            await session.execute("""
                INSERT INTO project_members (project_id, user_id, role)
                VALUES (:pid, :cid, 'admin')
            """, {"pid": project_id, "cid": creator_id})
            await session.commit()
        return project_id

    async def get_user_projects(self, user_id: str) -> List[Dict[str, Any]]:
        async with db_manager.get_session() as session:
            res = await session.execute("""
                SELECT p.* FROM collaborative_projects p
                JOIN project_members m ON p.project_id = m.project_id
                WHERE m.user_id = :uid
            """, {"uid": user_id})
            return [dict(r) for r in res]

class EcosystemManager:
    """Phases 40 & 41: Knowledge Market & Skill Economy."""
    async def create_listing(self, owner_id: str, l_type: str, title: str, price: float):
        listing_id = str(uuid.uuid4())
        async with db_manager.get_session() as session:
            await session.execute("""
                INSERT INTO ecosystem_listings (listing_id, owner_id, type, title, price_value)
                VALUES (:id, :oid, :type, :title, :price)
            """, {"id": listing_id, "oid": owner_id, "type": l_type, "title": title, "price": price})
            await session.commit()
        return listing_id

    async def get_active_listings(self) -> List[Dict[str, Any]]:
        async with db_manager.get_session() as session:
            res = await session.execute("SELECT * FROM ecosystem_listings WHERE status = 'active' ORDER BY created_at DESC")
            return [dict(r) for r in res]

reputation_manager = ReputationManager()
collab_manager = CollabManager()
ecosystem_manager = EcosystemManager()
