import logging
from .language_bridge_models import TranslatedSegment, VoiceStyle

logger = logging.getLogger(__name__)

class VoiceAdapter:
    """Adapts synthesized output to listener preferences for tone and style."""
    
    async def generate_speech_metadata(self, segment: TranslatedSegment, style: VoiceStyle) -> dict:
        """Determines parameters for the TTS engine based on style."""
        params = {
            "text": segment.translated_text,
            "language": segment.target_language.value,
            "style": style.value,
            "pitch": 1.0,
            "speed": 1.0
        }
        
        if style == VoiceStyle.SOFT:
            params["pitch"] = 0.9
            params["speed"] = 0.8
        elif style == VoiceStyle.ENERGETIC:
            params["pitch"] = 1.1
            params["speed"] = 1.2
        elif style == VoiceStyle.FORMAL:
            params["speed"] = 0.95
            
        logger.debug(f"Voice Adaptation: Applied '{style}' style to output.")
        return params

voice_adapter = VoiceAdapter()
