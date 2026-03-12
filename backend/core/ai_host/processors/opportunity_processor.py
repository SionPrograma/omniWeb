import logging
from typing import Dict, Any, Optional
from backend.core.opportunity_engine.opportunity_matcher import opportunity_matcher
from backend.core.skill_engine.skill_profile_builder import skill_profile_builder
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class OpportunityProcessor(CommandProcessor):
    """Handles requests for career direction and opportunities."""
    
    async def process(self, topic: str, user_id: str = "default_user") -> AICommandResponse:
        logger.info(f"Opportunity: User seeking opportunities in {topic}")
        
        # 1. Get Profile
        profile = skill_profile_builder.get_profile(user_id)
        
        # 2. Match
        matches = opportunity_matcher.find_matches(profile.top_skills)
        
        if not matches:
            return AICommandResponse(
                intent="opportunity_finder",
                message="Actualmente tu perfil está en fase de descubrimiento. Sigue aprendiendo para desbloquear oportunidades.",
                status="partial"
            )
            
        summary = "He identificado las siguientes **oportunidades de desarrollo** basadas en tu perfil actual:\n\n"
        for match in matches[:3]:
            summary += f"- **{match.title}** ({match.type}): {match.description}\n"
            
        return AICommandResponse(
            intent="opportunity_finder",
            message=summary,
            status="success",
            payload={"matches": [m.model_dump() for m in matches]}
        )

opportunity_processor = OpportunityProcessor()
