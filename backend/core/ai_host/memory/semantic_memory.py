import json
import os
import collections
from typing import List, Dict, Any, Optional
from datetime import datetime

class SemanticMemoryBuffer:
    """
    Short-term working memory for the AI Host.
    Retains recent interactions to provide conversational continuity.
    Now with persistent disk fallback.
    """
    def __init__(self, capacity: int = 50):
        self.capacity = capacity
        self.buffer = collections.deque(maxlen=capacity)
        self.storage_path = "backend/data/chat_memory.json"
        self._load_from_disk()

    def _load_from_disk(self):
        """Rehydrates memory from disk on startup."""
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Limit reload to current capacity
                    for item in data[-self.capacity:]:
                        self.buffer.append(item)
            except Exception as e:
                print(f"[MEMORY] Load error: {e}")

    def _save_to_disk(self):
        """Persists current buffer to disk."""
        try:
            os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump(list(self.buffer), f, default=str, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[MEMORY] Save error: {e}")

    def add_interaction(self, prompt: str, response: str, intent: str):
        """Adds a new interaction to the semantic buffer and persists it."""
        interaction = {
            "timestamp": datetime.now().isoformat(),
            "prompt": prompt,
            "response": response,
            "intent": intent
        }
        self.buffer.append(interaction)
        self._save_to_disk()

    def get_context_summary(self, max_items: int = 5) -> str:
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

    def get_recent_interactions(self, session_id: str = "default_user", limit: int = 5) -> List[Dict[str, Any]]:
        """Returns recent interactions for context enrichment. Increased default limit."""
        return list(self.buffer)[-limit:] if self.buffer else []

    def clear(self):
        """Resets the memory buffer and deletes the persistence file."""
        self.buffer.clear()
        if os.path.exists(self.storage_path):
            try:
                os.remove(self.storage_path)
            except: pass

# Global working memory instance
semantic_memory = SemanticMemoryBuffer()
