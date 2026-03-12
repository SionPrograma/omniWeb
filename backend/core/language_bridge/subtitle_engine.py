import logging
from typing import Dict, Any
from .language_bridge_models import TranslatedSegment, BridgeUserConfig

logger = logging.getLogger(__name__)

class SubtitleEngine:
    """Generates visual configuration for real-time translation subtitles."""
    
    def generate_display_data(self, segment: TranslatedSegment, config: BridgeUserConfig) -> Dict[str, Any]:
        """Provides the frontend-ready subtitle payload."""
        if not config.show_subtitles:
            return {"visible": False}

        # Styling logic based on user config
        font_size = "1.2rem"
        if config.subtitle_size == "small": font_size = "0.9rem"
        elif config.subtitle_size == "large": font_size = "1.5rem"

        return {
            "visible": True,
            "text": segment.translated_text,
            "style": {
                "font_size": font_size,
                "opacity": 0.9,
                "background": "rgba(0,0,0,0.6)",
                "color": "#00f2ff" # Holographic cyan
            },
            "position": "bottom-center"
        }

subtitle_engine = SubtitleEngine()
