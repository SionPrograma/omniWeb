from typing import Dict
import langdetect
import datetime
from backend.core.language_bridge.language_bridge_models import LanguageCode

class OnboardingManager:
    async def process_initial_greeting(self, user_id: str, text: str = None, browser_lang: str = "en") -> dict:
        """
        Detects language from initial greeting or browser hints and prepares the environment.
        """
        user_lang = LanguageCode.ENGLISH
        
        # 1. Detect Language
        if text:
            try:
                detected_lang = langdetect.detect(text)
                user_lang = self._map_lang(detected_lang)
            except:
                pass
        elif browser_lang:
            user_lang = self._map_lang(browser_lang.split('-')[0])

        # 2. Time of day logic
        now = datetime.datetime.now()
        hour = now.hour
        
        time_context = "morning"
        if 12 <= hour < 18:
            time_context = "afternoon"
        elif hour >= 18 or hour < 6:
            time_context = "evening"

        # 3. Returning User detection (Mocked via user_id check)
        # In production, this would query db_manager or memory_store
        is_returning = user_id != "new_user" and user_id != "default_user"

        greetings = {
            LanguageCode.SPANISH: {
                "morning": "¡Buenos días! Bienvenido de nuevo a OmniWeb." if is_returning else "¡Hola! Buenos días, bienvenido a OmniWeb, tu red de conocimiento.",
                "afternoon": "¡Buenas tardes! ¿En qué puedo ayudarte hoy?" if is_returning else "Hola, buenas tardes. Bienvenido a la plataforma OmniWeb.",
                "evening": "¡Buenas noches! Un placer verte de nuevo." if is_returning else "Buenas noches. Iniciando tu entorno de conocimiento OmniWeb."
            },
            LanguageCode.ENGLISH: {
                "morning": "Good morning! Welcome back to OmniWeb." if is_returning else "Hello! Good morning, welcome to OmniWeb, your knowledge network.",
                "afternoon": "Good afternoon! How can I help you today?" if is_returning else "Hello, good afternoon. Welcome to the OmniWeb platform.",
                "evening": "Good evening! Great to see you again." if is_returning else "Good evening. Initializing your OmniWeb knowledge environment."
            }
        }
        
        # Fallback to English if language not supported in greetings dict
        lang_greetings = greetings.get(user_lang, greetings[LanguageCode.ENGLISH])
        final_greeting = lang_greetings.get(time_context, lang_greetings["morning"])
        
        return {
            "detected_language": user_lang,
            "greeting": final_greeting,
            "time_context": time_context,
            "is_returning": is_returning,
            "setup_complete": True
        }

    def _map_lang(self, lang_code: str) -> LanguageCode:
        lang_map = {
            'es': LanguageCode.SPANISH,
            'en': LanguageCode.ENGLISH,
            'fr': LanguageCode.FRENCH,
            'de': LanguageCode.GERMAN,
            'ja': LanguageCode.JAPANESE,
            'zh': LanguageCode.CHINESE
        }
        return lang_map.get(lang_code, LanguageCode.ENGLISH)

onboarding_manager = OnboardingManager()
