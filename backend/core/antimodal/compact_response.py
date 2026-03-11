import logging
from typing import List, Optional
from .antimodal_models import AntimodalMode, CompactResponse

logger = logging.getLogger(__name__)

class CompactResponseGenerator:
    """
    Converts full AI responses into minimal, essential summaries.
    Requirement: in compact mode, long responses become concise summaries.
    """
    def __init__(self):
        pass

    def summarize(self, response: str, mode: AntimodalMode) -> CompactResponse:
        """
        Creates a compact version of a full AI response.
        """
        original_len = len(response)
        
        # Simple rule-based summarization (placeholder for more advanced NLP or LLM call)
        # 1. Split into sentences
        sentences = response.split(". ")
        
        if mode == AntimodalMode.SUMMARY_ONLY:
            # First and last sentences typically contain the core result and next action
            compact_text = f"{sentences[0]}... {sentences[-1]}"
            key_points = [sentences[0][:100], sentences[-1][:100]]
        elif mode == AntimodalMode.COMPACT:
            # Take only the first 2 sentences if many, or truncate if long
            limit = 2 if len(sentences) > 2 else 1
            compact_text = ". ".join(sentences[:limit])
            if len(sentences) > limit:
                 compact_text += "..."
            key_points = [s[:100] for s in sentences[:limit]]
        else:
            compact_text = response
            key_points = []
            
        # Safety: If compact is somehow longer, use original
        if len(compact_text) >= original_len and mode != AntimodalMode.STANDARD:
            compact_text = response[:max(original_len - 3, 0)] + "..."

        # Guess actions taken from text if possible
        actions = []
        if "abriendo" in response.lower() or "opening" in response.lower():
            actions.append("chip_activation")
        if "guardado" in response.lower() or "saved" in response.lower():
            actions.append("data_persistence")

        return CompactResponse(
            original_length=original_len,
            compact_text=compact_text,
            key_points=key_points,
            actions_taken=actions,
            mode_applied=mode
        )

response_generator = CompactResponseGenerator()
