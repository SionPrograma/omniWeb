import asyncio
import logging
import time
from typing import Dict
from .node_registry import node_registry

logger = logging.getLogger(__name__)

class NodeHealthMonitor:
    """
    Background service that monitors connectivity and health of remote nodes.
    """
    def __init__(self):
        self.latency_map: Dict[str, float] = {}
        self._running = False

    async def start(self):
        self._running = True
        asyncio.create_task(self._monitor_loop())
        logger.info("NodeHealthMonitor: Started monitoring loop.")

    def stop(self):
        self._running = False

    async def _monitor_loop(self):
        while self._running:
            active_nodes = node_registry.get_active_nodes()
            for node in active_nodes:
                if node.node_id == node_registry.local_node_id:
                    continue
                
                # Check latency (mocked for now, would be a real ping/check)
                await self._ping_node(node.node_id, node.node_address)
            
            await asyncio.sleep(15) # Check every 15 seconds

    async def _ping_node(self, node_id: str, address: str):
        start_time = time.time()
        try:
            # Simulate network check
            await asyncio.sleep(0.05) 
            latency = (time.time() - start_time) * 1000
            self.latency_map[node_id] = latency
            node_registry.heartbeat(node_id)
        except Exception as e:
            logger.warning(f"NodeHealthMonitor: Failed to ping node {node_id}: {e}")
            # Registry will eventually mark it as inactive due to lack of heartbeats

    def get_latency(self, node_id: str) -> float:
        return self.latency_map.get(node_id, -1.0)

node_health_monitor = NodeHealthMonitor()
