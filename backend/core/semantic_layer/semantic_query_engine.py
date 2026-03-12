import logging
from typing import List
from .embedding_engine import embedding_engine
from .vector_store import vector_store
from .concept_similarity import concept_similarity
from .embedding_models import SemanticSearchResult

logger = logging.getLogger(__name__)

class SemanticQueryEngine:
    """
    Performs similarity search across the semantic knowledge base.
    """
    def search(self, query: str, limit: int = 5, threshold: float = 0.5) -> List[SemanticSearchResult]:
        """
        Embeds the query and finds the most similar components.
        """
        query_vector = embedding_engine.generate_embedding(query)
        all_entries = vector_store.get_all_embeddings()
        
        results = []
        for entry in all_entries:
            score = concept_similarity.cosine_similarity(query_vector, entry.embedding)
            if score >= threshold:
                results.append(SemanticSearchResult(
                    node_id=entry.node_id,
                    source_type=entry.source_type,
                    score=score,
                    text_content=entry.text_content
                ))
                
        # Sort by score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:limit]

semantic_query_engine = SemanticQueryEngine()
