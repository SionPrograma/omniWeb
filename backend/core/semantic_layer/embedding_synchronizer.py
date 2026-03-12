import logging
import asyncio
from typing import List
from .embedding_engine import embedding_engine
from .vector_store import vector_store
from .embedding_models import VectorEntry

logger = logging.getLogger(__name__)

class EmbeddingSynchronizer:
    """
    Synchronizes Knowledge Graph, Memories, and Chips with the semantic layer.
    """
    async def sync_all(self):
        """
        Full synchronization of all system components.
        """
        logger.info("Semantic Layer: Starting full synchronization...")
        await self.sync_knowledge_nodes()
        await self.sync_memories()
        logger.info("Semantic Layer: Synchronization complete.")

    async def sync_knowledge_nodes(self):
        from backend.core.knowledge_graph.graph_store import GraphStore
        store = GraphStore()
        nodes = store.get_all_nodes()
        
        for node in nodes:
            self.sync_node(node)
            
    def sync_node(self, node):
        text = f"{node.name}: {node.description or ''}"
        vector = embedding_engine.generate_embedding(text)
        entry = VectorEntry(
            node_id=f"kg_node_{node.id}",
            source_type="knowledge_node",
            embedding=vector,
            text_content=text
        )
        vector_store.upsert_embedding(entry)

    async def sync_memories(self):
        from backend.core.long_memory.memory_store import memory_store
        memories = memory_store.get_memories(limit=1000)
        
        for mem in memories:
            self.sync_memory(mem)

    def sync_memory(self, memory):
        text = f"{memory.title}: {memory.summary or ''} {memory.content or ''}"
        vector = embedding_engine.generate_embedding(text)
        entry = VectorEntry(
            node_id=f"memory_{memory.id}",
            source_type="memory",
            embedding=vector,
            text_content=text
        )
        vector_store.upsert_embedding(entry)

embedding_synchronizer = EmbeddingSynchronizer()
