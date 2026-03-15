import logging
from typing import Optional

logger = logging.getLogger(__name__)


class TranslationAdapter:
    """
    OMNIWEB TRANSLATION ADAPTER (Phase 4)
    Bridges the Communication Layer with the existing Language Bridge (TranslationEngine).
    Auto-translates messages based on sender/receiver language preferences.
    """

    # Simulated dictionary for common phrases (extends Language Bridge)
    TRANSLATIONS = {
        "es": {
            "en": {
                "llegaré tarde": "I will arrive late",
                "estoy en camino": "I am on my way",
                "nos vemos luego": "see you later",
                "gracias por todo": "thanks for everything",
                "buen trabajo": "good job",
                "necesito ayuda": "I need help",
                "todo bien": "all good",
                "hablamos después": "we'll talk later",
                "envía los documentos": "send the documents",
                "reunión mañana": "meeting tomorrow",
            },
            "fr": {
                "llegaré tarde": "j'arriverai en retard",
                "estoy en camino": "je suis en route",
                "gracias por todo": "merci pour tout",
            },
            "de": {
                "llegaré tarde": "ich komme spät",
                "estoy en camino": "ich bin unterwegs",
            }
        },
        "en": {
            "es": {
                "i will arrive late": "llegaré tarde",
                "i am on my way": "estoy en camino",
                "see you later": "nos vemos luego",
                "thanks for everything": "gracias por todo",
                "good job": "buen trabajo",
                "i need help": "necesito ayuda",
                "all good": "todo bien",
                "send the documents": "envía los documentos",
                "meeting tomorrow": "reunión mañana",
            },
            "fr": {
                "i will arrive late": "j'arriverai en retard",
                "i am on my way": "je suis en route",
            }
        }
    }

    async def translate_text(self, text: str, source_lang: str, target_lang: str) -> Optional[str]:
        """
        Translates text from source language to target language.
        First checks the local dictionary, then falls back to the Language Bridge.
        """
        if source_lang == target_lang:
            return text

        text_lower = text.lower().strip()

        # Try local dictionary first
        translations = self.TRANSLATIONS.get(source_lang, {}).get(target_lang, {})
        if text_lower in translations:
            result = translations[text_lower]
            logger.info(f"Translated (local): '{text}' [{source_lang}] → '{result}' [{target_lang}]")
            return result

        # Try Language Bridge integration
        try:
            from backend.core.language_bridge.translation_engine import translation_engine
            from backend.core.language_bridge.language_bridge_models import ConversationSegment, LanguageCode
            import time

            # Map language codes
            lang_map = {
                "es": LanguageCode.SPANISH,
                "en": LanguageCode.ENGLISH,
                "fr": LanguageCode.FRENCH,
                "de": LanguageCode.GERMAN,
                "ar": LanguageCode.ARABIC,
                "ja": LanguageCode.JAPANESE,
                "zh": LanguageCode.CHINESE,
            }

            target_code = lang_map.get(target_lang)
            source_code = lang_map.get(source_lang)

            if target_code and source_code:
                segment = ConversationSegment(
                    speaker_id="system",
                    original_text=text,
                    original_language=source_code,
                    timestamp=time.time(),
                    duration=0.0
                )
                translated = await translation_engine.translate(segment, target_code)
                logger.info(f"Translated (bridge): '{text}' [{source_lang}] → '{translated.translated_text}' [{target_lang}]")
                return translated.translated_text
        except Exception as e:
            logger.warning(f"Language Bridge fallback failed: {e}")

        # Final fallback: tag the message
        fallback = f"[{target_lang.upper()}] {text}"
        logger.info(f"Translation fallback: '{text}' → '{fallback}'")
        return fallback


translation_adapter = TranslationAdapter()
