import logging
from typing import Dict, Any
from ..domain_bridge import DomainBridge
from ..event_bus import integration_bus
from backend.core.certification_engine.manager import certification_engine
from backend.core.opportunity_engine.opportunity_matcher import opportunity_matcher

logger = logging.getLogger(__name__)

class PipelineBridge(DomainBridge):
    """
    Orchestrates the Skill -> Certification -> Opportunity flow.
    Automates the advancement of users across professional domains.
    """
    def __init__(self):
        super().__init__("pipeline_bridge", ["skill_engine", "certification_engine", "opportunity_engine"])

    async def initialize(self):
        integration_bus.subscribe_to_domain("skill_threshold_reached", self.on_skill_threshold)
        integration_bus.subscribe_to_domain("certification_unlocked", self.on_certification_unlocked)
        logger.info("PipelineBridge: Global achievement pipelines active.")

    async def shutdown(self):
        pass

    async def on_skill_threshold(self, payload: Dict[str, Any]):
        """When a skill reaches a certain level, check for certification eligibility."""
        user_id = payload.get("user_id")
        skill_name = payload.get("skill_name")
        score = payload.get("score")
        
        logger.info(f"PipelineBridge: Skill '{skill_name}' threshold reached for {user_id}. Checking certifications...")
        
        # Trigger certification engine
        try:
            certs = await certification_engine.check_eligibility(user_id, skill_name, score)
            for cert in certs:
                await integration_bus.emit_domain_event(
                    "certification_eligible",
                    {"user_id": user_id, "cert_id": cert.id, "skill": skill_name},
                    "pipeline_bridge"
                )
        except Exception as e:
            logger.error(f"PipelineBridge: Eligibility check failed: {e}")

    async def on_certification_unlocked(self, payload: Dict[str, Any]):
        """When a certification is unlocked, matching it with opportunities."""
        user_id = payload.get("user_id")
        cert_id = payload.get("cert_id")
        
        logger.info(f"PipelineBridge: Cert '{cert_id}' unlocked for {user_id}. Finding opportunities...")
        
        # Trigger opportunity matching
        try:
            matches = await opportunity_matcher.match_for_user(user_id)
            if matches:
                await integration_bus.emit_domain_event(
                    "opportunity_found",
                    {"user_id": user_id, "matches_count": len(matches)},
                    "opportunity_engine"
                )
        except Exception as e:
            logger.error(f"PipelineBridge: Opportunity matching failed: {e}")

pipeline_bridge = PipelineBridge()
