import logging
from typing import List, Dict, Any, Optional
from backend.core.knowledge_graph.graph_store import GraphStore
from backend.core.knowledge_graph.graph_models import KnowledgeNode, KnowledgeEdge

logger = logging.getLogger(__name__)

class GraphQueryEngine:
    """
    Graph Query Engine provides high-level reasoning over the knowledge graph.
    Identifies relationships, dependency clusters and traversal logic.
    """
    def __init__(self):
        self.store = GraphStore()

    def get_related_topics(self, topic_name: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Finds topics connected to a given topic name."""
        node = self.store.find_node_by_name(topic_name)
        if not node:
            return []
            
        neighbors = self.store.get_neighbors(node.id)
        # Filter for top unique related nodes
        related = []
        seen = set()
        for n in neighbors:
            n_name = n["neighbor_name"]
            if n_name != topic_name and n_name not in seen:
                related.append({
                    "name": n_name,
                    "type": n["neighbor_type"],
                    "relationship": n["relationship"]
                })
                seen.add(n_name)
        
        return related[:limit]

    def get_project_graph(self, project_name: str) -> Dict[str, Any]:
        """Returns nodes and edges directly related to a project."""
        node = self.store.find_node_by_name(project_name, node_type="project")
        if not node:
            return {"nodes": [], "edges": []}
            
        nodes = [node]
        neighbors = self.store.get_neighbors(node.id)
        edges = neighbors # in simpler form
        
        # Also include neighbors as nodes
        for neighbor in neighbors:
            neigh_node = self.store.get_node(neighbor["target_node"] if neighbor["source_node"] == node.id else neighbor["source_node"])
            if neigh_node:
                nodes.append(neigh_node)
                
        return {"nodes": nodes, "edges": edges}

    def suggest_learning_path(self, start_topic: str) -> List[Dict[str, Any]]:
        """
        Suggests a progression of topics based on LEADS_TO or REQUIRES relationships.
        Calculates a simple path of related learning concepts.
        """
        node = self.store.find_node_by_name(start_topic)
        if not node:
            return []
            
        path = [{"name": node.name, "type": node.node_type}]
        neighbors = self.store.get_neighbors(node.id)
        
        # Heuristic: Priority for LEADS_TO, REQUIRES or high weight relationships
        for n in neighbors:
            if n["relationship"] in ["LEADS_TO", "REQUIRES", "PART_OF"]:
                path.append({
                    "name": n["neighbor_name"],
                    "type": n["neighbor_type"],
                    "relationship": n["relationship"]
                })
                # For basic logic, just take first strong connection
                break
                
        return path

    def get_connected_workflows(self, chip_name: str) -> List[str]:
        """Lists workflows that interact with a specific chip node."""
        node = self.store.find_node_by_name(chip_name, node_type="chip")
        if not node:
            return []
            
        neighbors = self.store.get_neighbors(node.id)
        workflows = [n["neighbor_name"] for n in neighbors if n["neighbor_type"] == "workflow"]
        return workflows
