import logging
from typing import Optional
from .interface_adapter import MultimodalInterface

logger = logging.getLogger(__name__)

class VoiceInterface(MultimodalInterface):
    """
    Adapter for Speech-to-Text (STT) systems.
    Can be connected to local Whisper or cloud-based engines.
    """
    def __init__(self, provider: str = "simulation"):
        self.provider = provider

    def normalize(self, audio_data: bytes) -> str:
        """
        Simulates or executes STT processing.
        In simulation mode, it assumes the 'audio' is a string for testing.
        """
        if self.provider == "simulation":
            # In simulation, we assume audio_data is already a pre-processed string
            # or a specific token.
            if isinstance(audio_data, str):
                return audio_data
            return "Comando de voz detectado (Simulado)"
        
        # Real implementation would call a Whisper instance here
        logger.info("Processing voice input with provider: %s", self.provider)
        return "Not implemented: Real STT"

    def generate_speech(self, text: str) -> Optional[bytes]:
        """Optionally converts text back to speech (TTS)."""
        logger.info("Generating speech for: %s", text[:30])
        return None
