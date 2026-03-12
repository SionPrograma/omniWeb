import logging
from typing import List
from .economy_models import Opportunity
from backend.core.skill_engine.skill_models import SkillProfile

logger = logging.getLogger(__name__)

class ProjectMatcher:
    """Matches user skill profiles with available global opportunities."""
    
    def match(self, profile: SkillProfile, pool: List[Opportunity]) -> List[Opportunity]:
        matches = []
        user_skills = set(profile.top_skills)
        
        for opp in pool:
            # Intersection of skills
            matching_skills = set(opp.required_skills).intersection(user_skills)
            match_score = len(matching_skills) / len(opp.required_skills) if opp.required_skills else 1.0
            
            if match_score > 0.4: # 40% threshold
                matches.append(opp)
                
        return sorted(matches, key=lambda x: len(set(x.required_skills).intersection(user_skills)), reverse=True)

project_matcher = ProjectMatcher()
