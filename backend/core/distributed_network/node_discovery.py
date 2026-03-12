import logging
import asyncio
import time
from typing import Dict, Any
from .node_registry import network_node_registry, KnowledgeSummary, NodeCapabilities

logger = logging.getLogger(__name__)

class NodeDiscovery:
    """
    Handles discovery of other OmniWeb nodes via the distributed event bus.
    Broadcasts local knowledge summary and heartbeats.
    """
    def __init__(self):
        self._running = False
        self._task = None

    async def start(self):
        if self._running:
            return
        self._running = True
        self._task = asyncio.create_task(self._discovery_loop())
        logger.info("NodeDiscovery: Service started.")

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        logger.info("NodeDiscovery: Service stopped.")

    async def _discovery_loop(self):
        """Periodically broadcasts the local node's presence and knowledge summary."""
        while self._running:
            try:
                # 1. Gather local knowledge summary
                summary = await self._generate_local_summary()
                
                # 2. Update local registry entry
                network_node_registry.update_knowledge_summary(
                    network_node_registry.local_node_id, 
                    summary
                )

                # 3. Broadcast presence to the network via Event Bus
                from backend.core.distributed_bus.distributed_event_router import distributed_event_router
                
                payload = {
                    "node_id": network_node_registry.local_node_id,
                    "node_url": "http://localhost:8000", # Should be dynamically resolved
                    "capabilities": {
                        "has_ai_host": True,
                        "has_knowledge_graph": True,
                        "has_semantic_layer": True,
                        "can_sync": True
                    },
                    "knowledge_summary": summary.dict(),
                    "timestamp": time.time()
                }

                await distributed_event_router.route_outgoing(
                    "network_node_heartbeat", 
                    payload,
                    chip_context="core"
                )

                # 4. Wait for next cycle
                await asyncio.sleep(30) # 30s heartbeat
                
            except Exception as e:
                logger.error(f"NodeDiscovery: Loop error: {e}")
                await asyncio.sleep(10)

    async def _generate_local_summary(self) -> KnowledgeSummary:
        """Collects metrics from KG and Semantic Layer for the summary."""
        try:
            from backend.core.knowledge_graph.graph_store import graph_store
            from backend.core.semantic_layer.vector_store import vector_store
            
            # Simple counts
            nodes = graph_store.get_all_nodes()
            num_nodes = len(nodes)
            
            # Try to get top concepts from semantic summary
            semantic_summary = vector_store.get_summary()
            num_embeddings = semantic_summary.get("total_indexed", 0)
            recent = [c["text"] for c in semantic_summary.get("recent_concepts", [])]
            
            return KnowledgeSummary(
                node_count=num_nodes,
                embedding_count=num_embeddings,
                top_concepts=recent[:5],
                last_updated=time.time()
            )
        except Exception as e:
            logger.error(f"NodeDiscovery: Failed to generate summary: {e}")
            return KnowledgeSummary(last_updated=time.time())

    async def handle_remote_heartbeat(self, payload: Dict[str, Any]):
        """Callback for incoming heartbeats from the event bus."""
        node_id = payload.get("node_id")
        if not node_id or node_id == network_node_registry.local_node_id:
            return

        # Register or update remote node
        caps = NodeCapabilities(**payload.get("capabilities", {}))
        summary = KnowledgeSummary(**payload.get("knowledge_summary", {}))
        
        network_node_registry.register_node(
            node_id=node_id,
            node_url=payload.get("node_url", "unknown"),
            capabilities=caps,
            knowledge_summary=summary
        )

node_discovery = NodeDiscovery()
