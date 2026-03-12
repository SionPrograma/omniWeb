from typing import List
from backend.core.skill_engine.skill_models import SkillProfile
from backend.core.knowledge_domains.domain_models import DomainCategory

class OpportunityMatcher:
    def match_user_to_projects(self, profile: SkillProfile, available_projects: List[dict]):
        """Matches a user's cognitive profile to active global projects."""
        matches = []
        for p in available_projects:
            # Simplified matching logic
            score = 0.0
            p_domain = p.get("domain")
            p_id = p.get("id")
            
            # Check if any skill matches domain
            for skill in profile.top_skills:
                if skill.lower() in str(p_domain).lower():
                    score += 0.5
            
            # Check cognitive metrics
            if profile.cognitive_metrics.get("systems_thinking") and profile.cognitive_metrics["systems_thinking"].score > 0.7:
                score += 0.3
                
            if score > 0.4:
                matches.append({"project_id": p_id, "match_score": score})
                
        return sorted(matches, key=lambda x: x["match_score"], reverse=True)

opportunity_matcher = OpportunityMatcher()
