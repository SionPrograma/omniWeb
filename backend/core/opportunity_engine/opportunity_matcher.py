import logging
import json
import random
from typing import List, Dict, Any
from .opportunity_models import Opportunity, MarketDemand
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class OpportunityMatcher:
    """Matches user skill profiles with available local and network opportunities."""
    
    def __init__(self):
        # Simulated job market demand
        self.market_demand = [
            MarketDemand(skill_name="thermodynamics", demand_level=0.8, trending=True, salary_range="Competitive"),
            MarketDemand(skill_name="programming", demand_level=0.9, trending=True),
            MarketDemand(skill_name="mechanical_systems", demand_level=0.7, trending=False)
        ]

    def find_matches(self, user_skills: List[str]) -> List[Opportunity]:
        """Cross-references user skills with global demand and project openings."""
        results = []
        
        # 1. Matching Logic (Simplified)
        for skill in user_skills:
            demand = next((d for d in self.market_demand if d.skill_name.lower() == skill.lower()), None)
            
            if demand:
                results.append(Opportunity(
                    title=f"Advanced {skill.capitalize()} Project",
                    type="learning_project" if demand.demand_level < 0.5 else "collaboration",
                    description=f"High demand for {skill} detected. Engage in this mission to build reputation.",
                    required_skills=[skill],
                    match_score=demand.demand_level,
                    source="omniweb_market"
                ))
                
        # 2. Add some "Hidden Talents" opportunities based on trending topics
        for demand in self.market_demand:
            if demand.trending and demand.skill_name not in user_skills:
                results.append(Opportunity(
                    title=f"Reskill in {demand.skill_name.capitalize()}",
                    type="career_path",
                    description=f"Trending skill shortage detected: {demand.skill_name}. High ROI career move.",
                    required_skills=[demand.skill_name],
                    match_score=0.3, # Low match but high potential
                    source="omniweb_analyzer"
                ))
        
        return results

opportunity_matcher = OpportunityMatcher()
