import logging
from typing import Any, Optional, Dict
from .interface_adapter import MultimodalInput, MultimodalResponse
from .voice_interface import VoiceInterface
from .visual_response import VisualResponseEngine

logger = logging.getLogger(__name__)

class MultimodalRouter:
    """
    Orchestrates inputs from various modalities and routes them to the AI Host.
    Ensures a unified command stream.
    """
    def __init__(self):
        self.voice = VoiceInterface()
        self.visual = VisualResponseEngine()

    async def handle_input(self, input_data: MultimodalInput) -> str:
        """
        Normalizes input and returns a string command for the AI Host.
        """
        if input_data.modality == "text":
            return str(input_data.raw_data)
        
        if input_data.modality == "voice":
            return self.voice.normalize(input_data.raw_data)
        
        if input_data.modality == "gesture":
            logger.info("Gesture detected: %s", input_data.raw_data)
            return f"Execute gesture {input_data.raw_data}"
            
        return "Unknown modality"

    def format_response(self, text: str, visual_payload: Optional[Dict] = None) -> MultimodalResponse:
        """Wraps text and visual data into a unified response object."""
        return MultimodalResponse(
            text_message=text,
            visual_payload=visual_payload
        )

multimodal_router = MultimodalRouter()
