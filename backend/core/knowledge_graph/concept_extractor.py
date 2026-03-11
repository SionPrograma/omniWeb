import re
import string
from typing import List, Set, Dict

class ConceptExtractor:
    """
    Extracted Topics and Concepts from memory-related text using Simple NLP.
    Tokenization, stopword filtering, importance scoring.
    """
    def __init__(self):
        # Broad stopword list for English and Spanish
        self.stopwords = {
            "a", "an", "the", "and", "or", "but", "if", "then", "else", "when", 
            "at", "by", "for", "from", "in", "of", "on", "to", "with", "is", "are", 
            "was", "were", "be", "been", "being", "have", "has", "had", "do", "does", "did",
            "la", "el", "los", "las", "un", "una", "unos", "unas", "de", "del", "al", "en",
            "y", "o", "pero", "si", "cuando", "con", "por", "para", "como", "esta", "esto",
            "este", "sus", "mi", "tu", "su", "que", "es", "son", "fue", "eran", "ser", "ha", 
            "han", "habia", "hacer", "hace", "hizo", "sobre"
        }

    def clean_text(self, text: str) -> str:
        """Removes punctuation and lowecases text."""
        if not text:
            return ""
        text = text.lower()
        # Remove punctuation
        text = text.translate(str.maketrans('', '', string.punctuation))
        return text

    def extract_concepts(self, text: str, min_length: int = 3) -> List[Dict[str, any]]:
        """
        Extracts key terms from text and assigns an importance score.
        Returns list of dicts with 'name' and 'score'.
        """
        cleaned = self.clean_text(text)
        words = cleaned.split()
        
        # Filter stopwords and short words
        filtered = [w for w in words if w not in self.stopwords and len(w) >= min_length]
        
        # Count frequencies
        freq: Dict[str, int] = {}
        for w in filtered:
            freq[w] = freq.get(w, 0) + 1
            
        # Scoring logic (normalized frequency + simple importance heuristics)
        total_freq = sum(freq.values())
        if total_freq == 0:
            return []
            
        concepts = []
        for word, count in freq.items():
            # A simple score between 0 and 1
            score = min(count / total_freq * 5.0, 1.0)
            concepts.append({"name": word, "score": score})
            
        # Sort by score descending
        concepts.sort(key=lambda x: x["score"], reverse=True)
        return concepts

    def identify_type(self, term: str) -> str:
        """
        Attempts to guess node type. Defaults to 'topic'.
        Currently uses basic keyword matching for simple categorization.
        """
        term = term.lower()
        # Chip names are usually specific
        if term.startswith("chip-") or term.endswith("-chip"):
            return "chip"
        if term in ["workflow", "routine", "automation", "study"]:
            return "workflow"
        if term in ["project", "engine", "system", "simulation"]:
            return "project"
            
        return "topic"
