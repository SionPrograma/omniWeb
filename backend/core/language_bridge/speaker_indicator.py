import logging
from typing import Dict, Any
from .language_bridge_models import Speaker, LanguageCode

logger = logging.getLogger(__name__)

class SpeakerIndicator:
    """Manages visual metadata for the speaker active in a bridge session."""
    
    def get_indicator_data(self, speaker: Speaker) -> Dict[str, Any]:
        """Provides metadata for visual speaker indicators on the dashboard or spatial UI."""
        
        # Flag simulation
        flags = {
            LanguageCode.SPANISH: "🇪🇸",
            LanguageCode.ENGLISH: "🇺🇸",
            LanguageCode.ARABIC: "🇲🇦",
            LanguageCode.FRENCH: "🇫🇷",
            LanguageCode.GERMAN: "🇩🇪"
        }

        return {
            "speaker_name": speaker.name,
            "language_flag": flags.get(speaker.native_language, "🌐"),
            "language_code": speaker.native_language.value,
            "animation_state": "speaking"
        }

speaker_indicator = SpeakerIndicator()
