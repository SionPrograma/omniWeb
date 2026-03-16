from typing import List, Dict, Any, Optional
from datetime import datetime
import collections

class SemanticMemoryBuffer:
    """
    Short-term working memory for the AI Host.
    Retains recent interactions to provide conversational continuity.
    """
    def __init__(self, capacity: int = 10):
        self.capacity = capacity
        # Use simple in-memory storage for now, scoped to the singleton lifecycle
        self.buffer = collections.deque(maxlen=capacity)

    def add_interaction(self, prompt: str, response: str, intent: str):
        """Adds a new interaction to the semantic buffer."""
        interaction = {
            "timestamp": datetime.now(),
            "prompt": prompt,
            "response": response,
            "intent": intent
        }
        self.buffer.append(interaction)

    def get_context_summary(self, max_items: int = 3) -> str:
        """Returns a string summary of recent context for prompt enrichment."""
        if not self.buffer:
            return ""
        
        recent = list(self.buffer)[-max_items:]
        summary = "Capas de memoria reciente:\n"
        for i, item in enumerate(recent):
            summary += f"- {item['prompt']} -> {item['intent']}\n"
        return summary

    def get_last_intent(self) -> Optional[str]:
        """Returns the intent of the last interaction."""
        if self.buffer:
            return self.buffer[-1]["intent"]
        return None

    def get_last_topic(self) -> Optional[str]:
        """Returns the prompt of the last interaction to understand what we were doing."""
        if self.buffer:
            return self.buffer[-1]["prompt"]
        return None

    def clear(self):
        """Resets the memory buffer."""
        self.buffer.clear()

# Global working memory instance
semantic_memory = SemanticMemoryBuffer()
