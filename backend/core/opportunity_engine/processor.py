import logging
import uuid
from typing import List, Dict, Any
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class OpportunityEngine:
    """
    Phase 34: Opportunity & Work Engine.
    Transforms verified skills into internal or external income opportunities.
    """
    async def match_opportunities(self, user_id: str) -> List[Dict[str, Any]]:
        # 1. Fetch User Skills (Certs)
        async with db_manager.get_session() as session:
            res_certs = await session.execute("SELECT skill_name FROM skill_certifications WHERE user_id = :uid", {"uid": user_id})
            user_skills = [r["skill_name"] for r in res_certs]
            
            if not user_skills:
                return []

            # 2. Find matching opportunities
            # Simulated matching logic
            res_opps = await session.execute("SELECT * FROM work_opportunities WHERE status = 'open'")
            all_opps = [dict(r) for r in res_opps]
            
            matches = []
            for opp in all_opps:
                req_skills = opp["required_skills"] # List of skills
                if any(skill in user_skills for skill in req_skills):
                    matches.append(opp)
                    
            return matches

    async def create_opportunity(self, title: str, description: str, skills: List[str], reward: float):
        opp_id = str(uuid.uuid4())
        query = """
        INSERT INTO work_opportunities (opp_id, title, description, required_skills, reward_value)
        VALUES (:id, :title, :desc, :skills, :reward)
        """
        async with db_manager.get_session() as session:
            await session.execute(query, {
                "id": opp_id, "title": title, "desc": description,
                "skills": skills, "reward": reward
            })
            await session.commit()
        return opp_id

opportunity_engine = OpportunityEngine()
