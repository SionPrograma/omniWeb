import logging
from typing import List, Dict
from .economy_models import Opportunity, SkillDemand

logger = logging.getLogger(__name__)

class SkillMarketEngine:
    """Analyzes global trends to detect skill shortages and market value."""
    
    def __init__(self):
        self._demands: List[SkillDemand] = [
            SkillDemand(skill_name="distributed_systems", demand_level=0.9, growth_rate=0.2, avg_reward="high"),
            SkillDemand(skill_name="ai_orchestration", demand_level=0.95, growth_rate=0.3, avg_reward="very_high"),
            SkillDemand(skill_name="knowledge_graph_design", demand_level=0.7, growth_rate=0.1, avg_reward="medium")
        ]

    def get_market_trends(self) -> List[SkillDemand]:
        return self._demands

    def get_scarcity_index(self, skills: List[str]) -> float:
        # Conceptual logic: average of demand levels
        if not skills: return 0.0
        levels = [d.demand_level for d in self._demands if d.skill_name in skills]
        return sum(levels) / len(levels) if levels else 0.5

skill_market_engine = SkillMarketEngine()
