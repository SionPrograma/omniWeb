import logging
from typing import Any, Optional
from .node_registry import node_registry
from .event_serializer import event_serializer, DistributedEvent

logger = logging.getLogger(__name__)

class DistributedEventRouter:
    """
    Routes events between local bus and remote nodes.
    """
    def __init__(self):
        self._sync_manager = None # Will be set by sync manager

    def set_sync_manager(self, manager):
        self._sync_manager = manager

    async def route_outgoing(self, event_name: str, payload: Any, chip_context: Optional[str] = None):
        """
        Wraps a local event and prepares it for distribution if necessary.
        """
        # 1. Create Distributed Event
        dist_event = event_serializer.wrap_local_event(
            event_name=event_name,
            payload=payload,
            origin_node=node_registry.local_node_id,
            chip_context=chip_context
        )
        
        # 2. Distribute to other nodes via sync manager
        if self._sync_manager:
            await self._sync_manager.broadcast(dist_event)
        else:
            logger.debug("DistributedEventRouter: No sync manager active, skipping broadcast.")

    async def route_incoming(self, data: str):
        """
        Receives an event from another node and injects it into the local bus.
        """
        try:
            event = event_serializer.deserialize(data)
            
            # Prevent loopback (redundant check if transport layer is smart)
            if event.origin_node == node_registry.local_node_id:
                return

            logger.info(f"DistributedEventRouter: Incoming event '{event.event_name}' from {event.origin_node}")
            
            # Ingest into local event bus without re-broadcasting
            from backend.core.event_bus import event_bus
            # We bypass the normal publish to avoid infinite loops
            # We'll need a specialized 'ingest' method or flag on event_bus
            await self._ingest_to_local_bus(event)
            
        except Exception as e:
            logger.error(f"DistributedEventRouter: Failed to route incoming event: {e}")

    async def _ingest_to_local_bus(self, event: DistributedEvent):
        # Implementation depends on event_bus internals
        # For now, we call publish but we'll need to make sure it doesn't trigger remote routing again
        from backend.core.event_bus import event_bus
        # We'll mark the payload to indicate it's already distributed
        if isinstance(event.payload, dict):
            event.payload["_distributed_ignore"] = True
        
        await event_bus.publish(event.event_name, event.payload)

distributed_event_router = DistributedEventRouter()
