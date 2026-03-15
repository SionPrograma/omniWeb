import logging
from typing import Dict, Any
from ..domain_bridge import DomainBridge
from ..event_bus import integration_bus
from backend.core.insight_engine.engine import insight_engine

logger = logging.getLogger(__name__)

class MentorBridge(DomainBridge):
    """
    Connects the AI Mentor to all platform domains.
    Generates cross-domain insights based on detected patterns.
    """
    def __init__(self):
        super().__init__("mentor_bridge", ["mentor", "all"])

    async def initialize(self):
        integration_bus.subscribe_to_domain("skill_detected", self.on_activity)
        integration_bus.subscribe_to_domain("music_analyzed", self.on_activity)
        integration_bus.subscribe_to_domain("leadership_signal_detected", self.on_leadership)
        logger.info("MentorBridge: AI Personalization link active.")

    async def shutdown(self):
        pass

    async def on_activity(self, payload: Dict[str, Any]):
        user_id = payload.get("user_id", "default_user")
        # Logic to generate synthesized mentor insight
        # Example: if both logic and music are high, suggest 'spatial harmony' insight
        pass

    async def on_leadership(self, payload: Dict[str, Any]):
        user_id = payload.get("user_id")
        # Mentor encourages leadership role
        await insight_engine.generate_personalized_insight(
            user_id, 
            "Your contributions show strong leadership signals. Consider exploring Governance Advisor roles."
        )

mentor_bridge = MentorBridge()
