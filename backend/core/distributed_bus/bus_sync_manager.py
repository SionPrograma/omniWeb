import asyncio
import logging
import requests
from typing import List
from .node_registry import node_registry
from .event_serializer import event_serializer, DistributedEvent
from .distributed_event_router import distributed_event_router

logger = logging.getLogger(__name__)

class BusSyncManager:
    """
    Manages the physical transport of distributed events between nodes.
    """
    def __init__(self):
        distributed_event_router.set_sync_manager(self)
        self.retry_queue: List[DistributedEvent] = []

    async def broadcast(self, event: DistributedEvent):
        """
        Sends an event to all other active nodes.
        """
        nodes = node_registry.get_active_nodes()
        tasks = []
        
        for node in nodes:
            if node.node_id == node_registry.local_node_id:
                continue
            
            tasks.append(self._send_to_node(node.node_address, event))
            
        if tasks:
            await asyncio.gather(*tasks)

    async def _send_to_node(self, address: str, event: DistributedEvent):
        """
        Internal helper to send event via HTTP POST.
        """
        url = f"http://{address}/api/v1/system/bus/receive"
        try:
            # We use a thread pool or run in executor for synchronous requests
            # For this prototype, we'll use a simple loop
            loop = asyncio.get_event_loop()
            data = event_serializer.serialize(event)
            
            def do_post():
                try:
                    return requests.post(url, data=data, timeout=2.0, headers={"Content-Type": "application/json"})
                except Exception as e:
                    return e

            resp = await loop.run_in_executor(None, do_post)
            
            if isinstance(resp, Exception):
                 logger.warning(f"BusSyncManager: Failed to send event to {address}: {resp}")
            elif resp.status_code != 200:
                 logger.warning(f"BusSyncManager: Node {address} returned {resp.status_code}")
                 
        except Exception as e:
            logger.error(f"BusSyncManager: Critical failure sending to {address}: {e}")

bus_sync_manager = BusSyncManager()
