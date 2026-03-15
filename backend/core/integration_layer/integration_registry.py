import logging
from typing import Dict, Any, List, Optional
from .domain_bridge import DomainBridge

logger = logging.getLogger(__name__)

class IntegrationRegistry:
    """
    Registry for all OmniWeb domain bridges.
    Ensures that domain connections are tracked and manageable.
    """
    def __init__(self):
        self._bridges: Dict[str, DomainBridge] = {}

    def register_bridge(self, bridge: DomainBridge):
        if bridge.bridge_id in self._bridges:
            logger.warning(f"Bridge '{bridge.bridge_id}' already registered. Overwriting.")
        self._bridges[bridge.bridge_id] = bridge
        logger.info(f"Registered Domain Bridge: {bridge.bridge_id} connecting {bridge.domains}")

    def get_bridge(self, bridge_id: str) -> Optional[DomainBridge]:
        return self._bridges.get(bridge_id)

    def list_bridges(self) -> List[Dict[str, Any]]:
        return [b.get_status() for b in self._bridges.values()]

    async def initialize_all(self):
        for bridge in self._bridges.values():
            try:
                await bridge.initialize()
            except Exception as e:
                logger.error(f"Failed to initialize bridge '{bridge.bridge_id}': {e}")

    async def shutdown_all(self):
        for bridge in self._bridges.values():
            try:
                await bridge.shutdown()
            except Exception as e:
                logger.error(f"Failed to shutdown bridge '{bridge.bridge_id}': {e}")

integration_registry = IntegrationRegistry()
