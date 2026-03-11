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
        Adapts the response based on the current mode.
        """
        response = {
            "mode": self.mode.value,
            "text": text
        }
        
        if self.mode == InterfaceMode.TEXT:
            response["display_data"] = data or {}
        elif self.mode == InterfaceMode.VOICE:
            response["speech"] = text # Simple placeholder
            
        return response

# Default global adapter
adapter = InterfaceAdapter(InterfaceMode.TEXT)
