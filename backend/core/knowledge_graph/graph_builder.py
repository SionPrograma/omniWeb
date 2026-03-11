import logging
from typing import List, Dict, Any
from backend.core.long_memory.memory_store import memory_store
from backend.core.knowledge_graph.graph_store import GraphStore
from backend.core.knowledge_graph.concept_extractor import ConceptExtractor
from backend.core.knowledge_graph.graph_models import KnowledgeNode, KnowledgeEdge

logger = logging.getLogger(__name__)

class GraphBuilder:
    """
    The GraphBuilder connects Long Term Memory with the Knowledge Network.
    It processes memories to extract entities and build relational links.
    """
    def __init__(self):
        self.store = GraphStore()
        self.extractor = ConceptExtractor()

    def process_all_memories(self):
        """Processes all extant memories to build the initial graph."""
        memories = memory_store.get_memories(limit=200)
        logger.info(f"Processing {len(memories)} memories for graph building...")
        
        for mem in memories:
            self.process_single_memory(mem)

    def process_single_memory(self, memory: Any):
        """
        Extracts concepts from a single memory and connects them.
        Creates nodes for topics, projects, chips and session-based nodes.
        """
        # 1. Combine title and summary for extraction
        text = f"{memory.title} {memory.summary if memory.summary else ''}"
        concepts = self.extractor.extract_concepts(text)
        
        # 2. Get or create nodes for concepts
        concept_node_ids = []
        for c in concepts:
            node = KnowledgeNode(
                node_type=self.extractor.identify_type(c["name"]),
                name=c["name"],
                description=f"Concept identified from memory: {memory.title}",
                importance_score=c["score"]
            )
            node_id = self.store.save_node(node)
            concept_node_ids.append(node_id)

        # 3. Create edges linking concepts found in the same memory
        # This implies they are related contexts
        for i, src_id in enumerate(concept_node_ids):
            for target_id in concept_node_ids[i+1:]:
                edge = KnowledgeEdge(
                    source_node=src_id,
                    target_node=target_id,
                    relationship="RELATES_TO",
                    weight=0.5 # Default relationship weight
                )
                self.store.save_edge(edge)

        # 4. Create explicit links to project or chip if present
        if memory.source_chip:
            chip_node = KnowledgeNode(
                node_type="chip",
                name=memory.source_chip,
                description=f"Automated Chip node for {memory.source_chip}"
            )
            chip_id = self.store.save_node(chip_node)
            
            # Link each concept to the chip that generated the memory
            for c_id in concept_node_ids:
                self.store.save_edge(KnowledgeEdge(
                    source_node=chip_id,
                    target_node=c_id,
                    relationship="USES",
                    weight=1.0
                ))

        # 5. Connect memory context - create a 'session' or 'event' node if useful
        if memory.memory_type:
            type_node = KnowledgeNode(
                node_type="learning_domain" if memory.memory_type == "learning" else "session",
                name=f"type_{memory.memory_type}",
                description=f"Cluster for {memory.memory_type} memories"
            )
            type_id = self.store.save_node(type_node)
            for c_id in concept_node_ids:
                self.store.save_edge(KnowledgeEdge(
                    source_node=type_id,
                    target_node=c_id,
                    relationship="PART_OF",
                    weight=0.8
                ))
