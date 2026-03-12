import math
from typing import List

class ConceptSimilarity:
    """
    Utility for calculating similarity between semantic vectors.
    """
    @staticmethod
    def cosine_similarity(v1: List[float], v2: List[float]) -> float:
        """
        Calculates cosine similarity between two vectors.
        Assumes they are already normalized (standard in embedding engines).
        """
        if len(v1) != len(v2):
            return 0.0
            
        dot_product = sum(a * b for a, b in zip(v1, v2))
        
        # If not normalized, we would divide by magnitude. 
        # But we assume our embedding engine generates unit vectors.
        # Just in case:
        # mag1 = math.sqrt(sum(a*a for a in v1))
        # mag2 = math.sqrt(sum(b*b for b in v2))
        # return dot_product / (mag1 * mag2)
        
        return dot_product

concept_similarity = ConceptSimilarity()
