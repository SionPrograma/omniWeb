import logging
from typing import List, Dict, Any
from backend.core.knowledge_graph.graph_store import GraphStore
from backend.core.long_memory.memory_store import memory_store

logger = logging.getLogger(__name__)

class IdeaLinker:
    """Connects new ideas to existing Knowledge Graph nodes and Long Term Memories."""
    
    def __init__(self):
        self.graph_store = GraphStore()

    def find_links(self, topics: List[str]) -> Dict[str, List[str]]:
        """Finds matching node IDs and memory IDs for a set of topics."""
        node_links = []
        memory_links = []
        
        # Link to Knowledge Graph
        all_nodes = self.graph_store.get_all_nodes()
        for topic in topics:
            for node in all_nodes:
                if topic.lower() == node.name.lower():
                    node_links.append(str(node.id))
        
        # Link to Long Term Memory
        memories = memory_store.get_memories(limit=100)
        for topic in topics:
            for mem in memories:
                if topic.lower() in mem.content.lower():
                    memory_links.append(str(mem.id))
                    
        return {
            "nodes": list(set(node_links)),
            "memories": list(set(memory_links))
        }

idea_linker = IdeaLinker()
