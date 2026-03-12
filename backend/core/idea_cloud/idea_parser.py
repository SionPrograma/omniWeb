import logging
from typing import List, Dict, Any
from backend.core.semantic_layer.semantic_query_engine import semantic_query_engine
from backend.core.knowledge_graph.graph_store import GraphStore

logger = logging.getLogger(__name__)

class IdeaParser:
    """Extracts concepts and topics from raw ideas using the semantic layer and knowledge graph."""
    
    def __init__(self):
        self.graph_store = GraphStore()

    def extract_topics(self, text: str) -> List[str]:
        """Detects key concepts in the idea text."""
        # 1. Semantic Search for related concepts
        results = semantic_query_engine.search(text, limit=3)
        topics = [res.text_content for res in results if res.score > 0.4]
        
        # 2. Match with existing nodes in the graph
        all_nodes = self.graph_store.get_all_nodes()
        text_lower = text.lower()
        for node in all_nodes:
            if node.name.lower() in text_lower and node.name not in topics:
                topics.append(node.name)
        
        return list(set(topics))

    def analyze_intent(self, text: str) -> Dict[str, Any]:
        """Classifies the idea into a project, learning topic, or technology."""
        text = text.lower()
        category = "general"
        if any(w in text for w in ["build", "create", "make", "proyecto", "project"]):
            category = "project"
        elif any(w in text for w in ["learn", "study", "aprender", "understand"]):
            category = "learning"
        elif any(w in text for w in ["using", "con", "tecnología", "tech"]):
            category = "technology"
            
        return {"category": category, "text": text}

idea_parser = IdeaParser()
