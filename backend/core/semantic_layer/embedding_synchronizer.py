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
    async def sync_all(self, force: bool = False):
        """
        Incremental synchronization by default. Set force=True to re-index all.
        """
        logger.info(f"Semantic Layer: Starting {'full' if force else 'incremental'} synchronization...")
        existing_ids = set() if force else vector_store.get_all_ids()
        
        await self.sync_knowledge_nodes(existing_ids)
        await self.sync_memories(existing_ids)
        logger.info("Semantic Layer: Synchronization complete.")

    async def sync_knowledge_nodes(self, existing_ids: set):
        from backend.core.knowledge_graph.graph_store import GraphStore
        store = GraphStore()
        nodes = store.get_all_nodes()
        
        count = 0
        for node in nodes:
            node_id = f"kg_node_{node.id}"
            if node_id not in existing_ids:
                self.sync_node(node)
                count += 1
                if count % 10 == 0:
                    await asyncio.sleep(0.01) # Cooperate with event loop
        
        if count > 0:
            logger.info(f"Synchronized {count} new Knowledge Nodes.")
            
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

    async def sync_memories(self, existing_ids: set):
        from backend.core.long_memory.memory_store import memory_store
        memories = memory_store.get_memories(limit=1000)
        
        count = 0
        for mem in memories:
            node_id = f"memory_{mem.id}"
            if node_id not in existing_ids:
                self.sync_memory(mem)
                count += 1
                if count % 10 == 0:
                    await asyncio.sleep(0.01)
        
        if count > 0:
            logger.info(f"Synchronized {count} new Memories.")

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
