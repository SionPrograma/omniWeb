import logging
from typing import Any, Dict, Optional
from backend.core.event_bus import event_bus as global_bus

logger = logging.getLogger(__name__)

class IntegrationEventBus:
    """
    Connective nervous system for OmniWeb domains.
    Wraps the global bus with integration-specific patterns.
    """
    
    @staticmethod
    async def emit_domain_event(event_name: str, payload: Dict[str, Any], source_domain: str):
        """
        Emits an event originating from a specific domain.
        Ensures metadata is correctly attached for cross-domain tracking.
        """
        payload["_integration_metadata"] = {
            "source_domain": source_domain,
            "orchestrated": True
        }
        logger.info(f"IntegrationEvent: {source_domain} -> {event_name}")
        await global_bus.publish(event_name, payload)

    @staticmethod
    def subscribe_to_domain(event_name: str, handler: Any):
        """Registers a listener for an integration event."""
        global_bus.subscribe(event_name, handler)

# Functional interface
integration_bus = IntegrationEventBus()
