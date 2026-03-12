import logging
from typing import Dict
from .language_bridge_models import LanguageCode, ConversationSegment, TranslatedSegment

logger = logging.getLogger(__name__)

class TranslationEngine:
    """Orchestrates real-time translation of conversation segments."""
    
    def __init__(self):
        # Simulated translation dictionary for common phrases
        self._simulated_translations = {
            "hola": {LanguageCode.ENGLISH: "hello", LanguageCode.ARABIC: "salaam"},
            "cómo estás": {LanguageCode.ENGLISH: "how are you", LanguageCode.ARABIC: "kayfa halak"},
            "gracias": {LanguageCode.ENGLISH: "thank you", LanguageCode.ARABIC: "shukran"}
        }

    async def translate(self, segment: ConversationSegment, target_lang: LanguageCode) -> TranslatedSegment:
        """Translates a segment into the target language."""
        text_lower = segment.original_text.lower().strip()
        
        # Simulated translation logic
        translated_text = self._simulated_translations.get(text_lower, {}).get(target_lang)
        
        if not translated_text:
            # Fallback simulation
            translated_text = f"[{target_lang.upper()}] {segment.original_text}"

        logger.info(f"Translating: '{segment.original_text}' -> '{translated_text}' ({target_lang})")
        
        return TranslatedSegment(
            segment_id=segment.id,
            target_language=target_lang,
            translated_text=translated_text
        )

translation_engine = TranslationEngine()
