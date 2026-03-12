import hashlib
import random
import math
import logging
from typing import List

logger = logging.getLogger(__name__)

class EmbeddingEngine:
    """
    Generates semantic embeddings for text content.
    For this phase, we use a deterministic mock embedding logic without external dependencies (numpy-free).
    """
    def __init__(self, dimension: int = 128):
        self.dimension = dimension

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generates a deterministic vector. Improves matching by averaging word-based vectors.
        """
        if not text:
            return [0.0] * self.dimension
            
        import re
        # Clean and tokenize
        words = re.findall(r'\w+', text.lower())
        if not words:
            words = [text.lower()]

        final_vector = [0.0] * self.dimension
        
        for word in words:
            hash_digest = hashlib.sha256(word.encode('utf-8')).digest()
            seed = int.from_bytes(hash_digest[:4], 'big')
            rng = random.Random(seed)
            word_vector = [rng.uniform(-1, 1) for _ in range(self.dimension)]
            
            for i in range(self.dimension):
                final_vector[i] += word_vector[i]
        
        # Average
        for i in range(self.dimension):
            final_vector[i] /= len(words)

        # Calculate norm
        sum_sq = sum(x*x for x in final_vector)
        norm = math.sqrt(sum_sq)
        
        # Normalize
        if norm > 0:
            final_vector = [x / norm for x in final_vector]
        else:
            final_vector[0] = 1.0
            
        return final_vector

embedding_engine = EmbeddingEngine()
