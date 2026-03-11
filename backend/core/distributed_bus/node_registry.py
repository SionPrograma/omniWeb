import logging
import time
import uuid
from typing import Dict, List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

class NodeInfo(BaseModel):
    node_id: str
    node_type: str  # desktop, server, mobile, embedded, container
    node_address: str
    capabilities: List[str]
    last_seen: float
    status: str = "active"

class NodeRegistry:
    """
    Tracks all active OmniWeb nodes in a distributed environment.
    """
    def __init__(self):
        self.nodes: Dict[str, NodeInfo] = {}
        self.local_node_id = str(uuid.uuid4())
        self._initialize_local_node()

    def _initialize_local_node(self):
        # We'll set this from config/env later if needed
        from backend.core.config import settings
        self.register_node(
            node_id=self.local_node_id,
            node_type="desktop", # Default
            node_address="127.0.0.1:8000",
            capabilities=["ai_host", "chip_factory", "stability_loop"]
        )

    def register_node(self, node_id: str, node_type: str, node_address: str, capabilities: List[str]):
        node = NodeInfo(
            node_id=node_id,
            node_type=node_type,
            node_address=node_address,
            capabilities=capabilities,
            last_seen=time.time()
        )
        self.nodes[node_id] = node
        logger.info(f"NodeRegistry: Registered node {node_id} ({node_type}) at {node_address}")

    def heartbeat(self, node_id: str):
        if node_id in self.nodes:
            self.nodes[node_id].last_seen = time.time()
            self.nodes[node_id].status = "active"
        else:
            logger.warning(f"NodeRegistry: Heartbeat received for unknown node {node_id}")

    def get_active_nodes(self) -> List[NodeInfo]:
        now = time.time()
        # Mark as inactive if not seen for 30 seconds
        active_nodes = []
        for node in self.nodes.values():
            if now - node.last_seen < 30:
                active_nodes.append(node)
            else:
                node.status = "inactive"
        return active_nodes

    def remove_node(self, node_id: str):
        if node_id in self.nodes:
            del self.nodes[node_id]
            logger.info(f"NodeRegistry: Removed node {node_id}")

node_registry = NodeRegistry()
