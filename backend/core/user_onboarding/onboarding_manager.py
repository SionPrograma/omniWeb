from typing import Dict
import langdetect
from backend.core.language_bridge.language_bridge_models import LanguageCode

class OnboardingManager:
    async def process_initial_greeting(self, user_id: str, text: str) -> dict:
        """
        Detects language from initial greeting and prepares the environment.
        """
        try:
            detected_lang = langdetect.detect(text)
            # Map detected lang to our LanguageCode
            lang_map = {
                'es': LanguageCode.SPANISH,
                'en': LanguageCode.ENGLISH,
                'fr': LanguageCode.FRENCH,
                'de': LanguageCode.GERMAN,
                'it': LanguageCode.ENGLISH, # Italy as fallback to English if not in enum
                'pt': LanguageCode.ENGLISH, # Portugal as fallback to English
                'ja': LanguageCode.JAPANESE,
                'zh': LanguageCode.CHINESE
            }
            user_lang = lang_map.get(detected_lang, LanguageCode.ENGLISH)
        except:
            user_lang = LanguageCode.ENGLISH

        # In a real system, we would store this in the User's Personal Context
        # and update their UI preferences.
        
        greetings = {
            LanguageCode.SPANISH: "¡Hola! Bienvenido a OmniWeb, tu red global de conocimiento colaborativo.",
            LanguageCode.ENGLISH: "Hello! Welcome to OmniWeb, your global collaborative knowledge network.",
            LanguageCode.FRENCH: "Bonjour ! Bienvenue sur OmniWeb, votre réseau mondial de connaissances collaboratives.",
            LanguageCode.GERMAN: "Hallo! Willkommen bei OmniWeb, Ihrem globalen kollaborativen Wissensnetzwerk."
        }
        
        return {
            "detected_language": user_lang,
            "greeting": greetings.get(user_lang, greetings[LanguageCode.ENGLISH]),
            "setup_complete": True
        }

onboarding_manager = OnboardingManager()
