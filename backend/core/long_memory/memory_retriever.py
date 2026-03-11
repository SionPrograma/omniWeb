import logging
from typing import List, Dict, Any, Optional
from .memory_models import MemoryEntry
from .memory_store import memory_store
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class MemoryRetriever:
    """
    Retrieves relevant historical memories for the AI Host.
    """
    def find_relevant_memories(self, query: str, chip_slug: Optional[str] = None) -> List[MemoryEntry]:
        """
        Retrieves memories based on topic similarity (mocked for now) and context.
        """
        # Basic search logic: match keywords in title or summary
        all_memories = memory_store.get_memories(limit=100)
        query_words = query.lower().split()
        
        results = []
        for memory in all_memories:
            score = 0
            # Context bonus
            if chip_slug and memory.source_chip == chip_slug:
                score += 2
                
            # Content match
            for word in query_words:
                if word in memory.title.lower() or word in memory.summary.lower():
                    score += 1
            
            if score > 0:
                results.append((score, memory))
        
        # Sort by score and importance
        results.sort(key=lambda x: (x[0], x[1].importance_score), reverse=True)
        
        final_memories = [r[1] for r in results[:5]]
        
        # Update last accessed timestamp for retrieved memories
        self._update_access_timestamp([m.id for m in final_memories if m.id])
        
        return final_memories

    def _update_access_timestamp(self, memory_ids: List[int]):
        if not memory_ids: return
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    placeholders = ",".join(["?"] * len(memory_ids))
                    conn.execute(
                        f"UPDATE long_term_memories SET last_accessed_at = CURRENT_TIMESTAMP WHERE id IN ({placeholders})",
                        memory_ids
                    )
                    conn.commit()
            except Exception as e:
                logger.error(f"MemoryRetriever: Failed to update timestamps: {e}")

    def get_recent_projects(self) -> List[MemoryEntry]:
        return memory_store.get_memories(memory_type="project_memory", limit=5)

memory_retriever = MemoryRetriever()
