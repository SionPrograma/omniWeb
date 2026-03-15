import logging
from typing import Dict, Any
from ..domain_bridge import DomainBridge
from ..event_bus import integration_bus
from backend.core.communication.conversation_memory import conversation_memory

logger = logging.getLogger(__name__)

class CommunicationBridge(DomainBridge):
    """
    Integrates the Communication Layer with other domains.
    Links project activities, opportunities, and governance actions to messaging.
    """
    def __init__(self):
        super().__init__("communication_bridge", ["communication", "governance", "opportunity"])

    async def initialize(self):
        integration_bus.subscribe_to_domain("opportunity_found", self.on_opportunity_found)
        integration_bus.subscribe_to_domain("admin_action_required", self.on_admin_action)
        logger.info("CommunicationBridge: Messaging pipelines linked.")

    async def shutdown(self):
        pass

    async def on_opportunity_found(self, payload: Dict[str, Any]):
        """Notifies the user via communication system when a new opportunity is found."""
        user_id = payload.get("user_id")
        count = payload.get("matches_count", 1)
        
        message = f"OmniWeb Analysis: {count} new professional opportunities matched your profile. Check the Opportunity Engine."
        # In a real system, this might send an internal message/notification
        logger.info(f"CommunicationBridge: Triggering notification for {user_id}: {message}")

    async def on_admin_action(self, payload: Dict[str, Any]):
        """Alerts administrators via priority communication."""
        action_type = payload.get("action_type")
        logger.info(f"CommunicationBridge: Alerting admins for high-priority action: {action_type}")

communication_bridge = CommunicationBridge()
