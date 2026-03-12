import logging
import time
import uuid
from typing import Dict, List, Optional, Any
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class NodeCapabilities(BaseModel):
    has_ai_host: bool = True
    has_knowledge_graph: bool = True
    has_semantic_layer: bool = True
    can_sync: bool = True

class KnowledgeSummary(BaseModel):
    node_count: int = 0
    embedding_count: int = 0
    top_concepts: List[str] = []
    last_updated: float = 0.0

class NodeInfo(BaseModel):
    node_id: str
    node_url: str
    capabilities: NodeCapabilities
    knowledge_summary: KnowledgeSummary
    last_seen: float
    status: str = "active"

class NodeRegistry:
    """
    Advanced registry for Distributed OmniWeb Knowledge Network.
    Tracks specialized knowledge capabilities and health.
    """
    def __init__(self):
        self.nodes: Dict[str, NodeInfo] = {}
        self.local_node_id = str(uuid.uuid4())
        self._initialize_local_node()

    def _initialize_local_node(self):
        # Local node represents the current instance
        from backend.core.config import settings
        
        # Default local capabilities
        caps = NodeCapabilities(
            has_ai_host=True,
            has_knowledge_graph=True,
            has_semantic_layer=True,
            can_sync=True
        )
        
        # We start with empty summary, will be updated by discovery
        summary = KnowledgeSummary(
            node_count=0,
            embedding_count=0,
            top_concepts=[],
            last_updated=time.time()
        )

        self.register_node(
            node_id=self.local_node_id,
            node_url="http://localhost:8000", # Should be configurable
            capabilities=caps,
            knowledge_summary=summary
        )

    def register_node(self, node_id: str, node_url: str, capabilities: NodeCapabilities, knowledge_summary: KnowledgeSummary):
        node = NodeInfo(
            node_id=node_id,
            node_url=node_url,
            capabilities=capabilities,
            knowledge_summary=knowledge_summary,
            last_seen=time.time()
        )
        self.nodes[node_id] = node
        logger.info(f"DistributedNetwork: Registered node {node_id} at {node_url}")

    def update_knowledge_summary(self, node_id: str, summary: KnowledgeSummary):
        if node_id in self.nodes:
            self.nodes[node_id].knowledge_summary = summary
            self.nodes[node_id].last_seen = time.time()
            logger.info(f"DistributedNetwork: Updated knowledge summary for {node_id}")

    def get_active_nodes(self) -> List[NodeInfo]:
        now = time.time()
        active = []
        for node in self.nodes.values():
            if now - node.last_seen < 60: # 1 minute timeout
                active.append(node)
            else:
                node.status = "inactive"
        return active

    def get_node(self, node_id: str) -> Optional[NodeInfo]:
        return self.nodes.get(node_id)

network_node_registry = NodeRegistry()
