from enum import Enum
from typing import Optional

class InterfaceMode(Enum):
    TEXT = "text"
    VOICE = "voice"
    HOLOGRAPHIC = "holographic"

class InterfaceAdapter:
    """
    Abstraction layer for different AI Host interfaces.
    """
    def __init__(self, mode: InterfaceMode = InterfaceMode.TEXT):
        self.mode = mode

    def format_response(self, text: str, data: Optional[dict] = None) -> dict:
        """
        Adapts the response based on the current mode and adds multimodal logic.
        """
        response = {
            "mode": self.mode.value,
            "text": text,
            "payload": data or {}
        }
        
        # Multimodal Layer: Visual response generation (Phase J)
        if data and "visual" in data:
             response["visual"] = data["visual"]
        
        if self.mode == InterfaceMode.TEXT:
            response["display_data"] = data or {}
        elif self.mode == InterfaceMode.VOICE:
            response["speech"] = text
            
        return response

adapter = InterfaceAdapter(InterfaceMode.TEXT)
