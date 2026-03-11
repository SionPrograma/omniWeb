from typing import Any, Dict, Optional
from pydantic import BaseModel

class MultimodalInput(BaseModel):
    modality: str # text, voice, gesture, image
    raw_data: Any
    metadata: Dict[str, Any] = {}

class MultimodalResponse(BaseModel):
    text_message: str
    visual_payload: Optional[Dict[str, Any]] = None
    voice_payload: Optional[Any] = None

class MultimodalInterface:
    """
    Abstract Interface for Multimodal adaptivity.
    Defines how different input types are normalized into system actions.
    """
    def normalize(self, data: Any) -> str:
        """Converts raw modality data into a text-based natural language command."""
        raise NotImplementedError("Subclasses must implement normalize")
