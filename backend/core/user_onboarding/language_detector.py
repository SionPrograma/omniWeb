import logging
import asyncio
from typing import Optional
from backend.core.language_bridge.language_bridge_models import LanguageCode

logger = logging.getLogger(__name__)

class LanguageDetector:
    """Detects user language from initial interaction to personalize onboarding."""
    
    async def detect_from_text(self, text: str) -> LanguageCode:
        # Simple heuristic for simulation
        text = text.lower()
        if any(w in text for w in ["hola", "buenos", "días"]):
            return LanguageCode.SPANISH
        if any(w in text for w in ["hello", "morning", "hi"]):
            return LanguageCode.ENGLISH
        if any(w in text for w in ["salaam", "ahlan"]):
            return LanguageCode.ARABIC
            
        return LanguageCode.ENGLISH # Default fallback

language_detector = LanguageDetector()
