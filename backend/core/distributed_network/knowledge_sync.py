import logging
import httpx
from typing import List, Dict, Any
from backend.core.knowledge_graph.graph_store import graph_store
from backend.core.knowledge_graph.graph_models import KnowledgeNode, KnowledgeEdge
from backend.core.stability_loop.loop_controller import loop_controller
from .node_registry import network_node_registry

logger = logging.getLogger(__name__)

class KnowledgeSyncManager:
    """
    Manages synchronization of knowledge graph data between distributed nodes.
    Supports pull-based synchronization.
    """
    async def request_sync(self, remote_node_id: str):
        """Requests a knowledge bundle from a remote node and ingests it locally."""
        node = network_node_registry.get_node(remote_node_id)
        if not node:
            logger.error(f"KnowledgeSync: Node {remote_node_id} not found in registry.")
            return

        async def perform_sync():
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # 1. Fetch knowledge bundle from remote node
                    # Note: We need to implement this endpoint on the receiving side
                    response = await client.get(f"{node.node_url}/api/v1/network/knowledge/bundle")
                    if response.status_code != 200:
                        raise Exception(f"Failed to fetch bundle from {node.node_url}")
                    
                    bundle = response.json()
                    
                    # 2. Ingest nodes
                    nodes_data = bundle.get("nodes", [])
                    edges_data = bundle.get("edges", [])
                    
                    success_count = 0
                    for nd in nodes_data:
                        knode = KnowledgeNode(**nd)
                        # We strip the ID to let the local graph_store assign a new one or update by name/type
                        knode.id = None 
                        graph_store.save_node(knode)
                        success_count += 1
                        
                    # 3. Ingest edges (simplified: we'd need to map remote IDs to local IDs properly)
                    # For a robust implementation, we'd use consistent cross-node IDs
                    
                    return {"status": "success", "nodes_synced": success_count}
            except Exception as e:
                logger.error(f"KnowledgeSync error: {e}")
                raise e

        # Use Stability Loop to protect the local graph state
        loop_state, result = await loop_controller.execute_task(
            "knowledge_sync",
            perform_sync,
            {"source_node": remote_node_id}
        )
        return loop_state, result

    def get_local_bundle(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generates a bundle of local knowledge for other nodes to consume."""
        nodes = graph_store.get_all_nodes()
        # For simplicity, we just return nodes. Edges require mapping IDs.
        return {
            "nodes": [n.dict() for n in nodes],
            "edges": [] 
        }

knowledge_sync_manager = KnowledgeSyncManager()
