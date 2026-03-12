import logging
from typing import List, Optional
from .education_models import ConceptNode
from backend.core.knowledge_graph.graph_store import GraphStore

logger = logging.getLogger(__name__)

class ConceptMapBuilder:
    """Recursively builds tree structures of concepts for visualization."""
    
    def __init__(self):
        self.graph_store = GraphStore()

    def build_map(self, topic_name: str, depth: int = 2) -> Optional[ConceptNode]:
        node = self.graph_store.find_node_by_name(topic_name)
        if not node:
            return ConceptNode(id="unknown", name=topic_name)
            
        root = ConceptNode(id=str(node.id), name=node.name)
        
        if depth > 0:
            neighbors = self.graph_store.get_neighbors(node.id)
            for neighbor in neighbors:
                child = self.build_map(neighbor['neighbor_name'], depth - 1)
                if child:
                    root.children.append(child)
                    
        return root

concept_map_builder = ConceptMapBuilder()
