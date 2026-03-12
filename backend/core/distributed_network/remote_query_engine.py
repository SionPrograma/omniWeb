import logging
import httpx
import asyncio
from typing import List, Dict, Any, Optional
from backend.core.semantic_layer.search_engine import semantic_query_engine
from .node_registry import network_node_registry, NodeInfo

logger = logging.getLogger(__name__)

class RemoteQueryEngine:
    """
    Decentralized query engine that searches both local and remote knowledge nodes.
    Supports federated semantic search.
    """
    async def federated_search(self, query: str, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """
        1. Local search
        2. Remote search broadcast to all active nodes
        3. Merge results based on semantic relevance
        """
        # 1. Local Search
        local_results = await semantic_query_engine.search(query, threshold=threshold)
        for res in local_results:
            res["origin_node"] = "local"
        
        # 2. Remote Search Broadcast
        active_nodes = network_node_registry.get_active_nodes()
        remote_tasks = []
        for node in active_nodes:
            if node.node_id != network_node_registry.local_node_id:
                remote_tasks.append(self._query_node(node, query, threshold))
        
        if not remote_tasks:
            return local_results
        
        # 3. Gather remote results
        remote_responses = await asyncio.gather(*remote_tasks, return_exceptions=True)
        
        # 4. Merge results
        all_results = local_results.copy()
        for resp in remote_responses:
            if isinstance(resp, list):
                all_results.extend(resp)
            elif isinstance(resp, Exception):
                logger.warning(f"RemoteQuery: Failed to query node: {resp}")
                
        # 5. Re-sort by score
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        
        # Limit to top results for the response
        return all_results[:10]

    async def _query_node(self, node: NodeInfo, query: str, threshold: float) -> List[Dict[str, Any]]:
        """Queries a single remote node for semantic matches."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{node.node_url}/api/v1/network/knowledge/search", 
                    params={"query": query, "threshold": threshold}
                )
                if response.status_code == 200:
                    results = response.json()
                    for r in results:
                        r["origin_node"] = node.node_id
                        r["node_url"] = node.node_url
                    return results
                return []
        except Exception as e:
            logger.error(f"RemoteQuery: Failed to reach node {node.node_id}: {e}")
            return []

remote_query_engine = RemoteQueryEngine()
