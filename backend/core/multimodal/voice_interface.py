import logging
from typing import Any, Dict, Optional
from .interface_adapter import MultimodalInterface

logger = logging.getLogger(__name__)

class VoiceInterface(MultimodalInterface):
    """
    Adapter for Speech-to-Text (STT) systems.
    Can be connected to local Whisper or cloud-based engines.
    """
    def __init__(self, provider: str = "simulation"):
        self.provider = provider

    def normalize(self, audio_data: Any) -> str:
        """
        Transforms raw voice signal into a system-ready intent bundle.
        """
        text = "Comando de voz (Simulado)"
        if isinstance(audio_data, str):
            text = audio_data
        
        logger.info(f"[VOICE] Normalizing: '{text[:20]}...'")
        
        return text
        
        # Real implementation would call a Whisper instance here
        logger.info("Processing voice input with provider: %s", self.provider)
        return "Not implemented: Real STT"

    def generate_speech(self, text: str) -> Optional[bytes]:
        """Optionally converts text back to speech (TTS)."""
        logger.info("Generating speech for: %s", text[:30])
        return None
