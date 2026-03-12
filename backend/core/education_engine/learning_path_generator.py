import logging
from typing import List, Optional
from .education_models import LearningPath, LearningStep
from backend.core.semantic_layer.semantic_query_engine import semantic_query_engine
from backend.core.knowledge_graph.graph_store import GraphStore

logger = logging.getLogger(__name__)

class LearningPathGenerator:
    """Generates structured sequences of concepts for users to study."""
    
    def __init__(self):
        self.graph_store = GraphStore()

    def generate_path(self, topic: str) -> LearningPath:
        logger.info(f"Education: Generating path for {topic}")
        
        # 1. Start with the main topic
        steps = []
        
        # 2. Use Semantic Query to find related prerequisites or components
        results = semantic_query_engine.search(topic, limit=10)
        
        # 3. Filter and structure into steps
        # Simple heuristic: main topic first, then neighbors from KG
        main_node = self.graph_store.find_node_by_name(topic)
        
        if main_node:
            neighbors = self.graph_store.get_neighbors(main_node.id)
            # Add prerequisites if tagged in metadata (simplified for v1.0)
            steps.append(LearningStep(
                title=f"Introduction to {topic}",
                description=f"Understanding the core fundamentals of {topic}.",
                concepts=[topic]
            ))
            
            for neighbor in neighbors[:4]:
                steps.append(LearningStep(
                    title=f"Exploring {neighbor['neighbor_name']}",
                    description=f"How it relates to {topic} through {neighbor['relationship']}.",
                    concepts=[neighbor['neighbor_name']]
                ))
        else:
            # Fallback to semantic results if no KG node exists
            steps.append(LearningStep(
                title=f"Introduction to {topic}",
                description=f"Overview of {topic}.",
                concepts=[topic]
            ))
            for res in results[:4]:
                steps.append(LearningStep(
                    title=f"Dive into {res.text_content[:20]}...",
                    description=res.text_content[:100],
                    concepts=[res.text_content]
                ))

        return LearningPath(topic=topic, steps=steps)

learning_path_generator = LearningPathGenerator()
