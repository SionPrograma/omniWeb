from typing import Dict
import langdetect
import datetime
from backend.core.language_bridge.language_bridge_models import LanguageCode

class OnboardingManager:
    def __init__(self):
        self.titles = {
            LanguageCode.SPANISH: "Omni Shell - Bienvenida",
            LanguageCode.ENGLISH: "Omni Shell - Welcome",
            LanguageCode.FRENCH: "Omni Shell - Bienvenue",
            LanguageCode.GERMAN: "Omni Shell - Willkommen",
            LanguageCode.JAPANESE: "Omni Shell - ようこそ",
            LanguageCode.CHINESE: "Omni Shell - 欢迎"
        }

    async def process_initial_greeting(self, user_id: str, text: str = None, browser_lang: str = "en", invite_token: str = None) -> dict:
        """
        Detects language from initial greeting or browser hints and prepares the environment.
        Initiates the Leadership Onboarding Protocol for Beta Testers.
        """
        user_lang = LanguageCode.ENGLISH
        
        # Verify Token (Protocol Step 1 Security)
        is_beta_tester = False
        if invite_token:
            try:
                from backend.core.database import db_manager
                with db_manager.get_connection() as conn:
                    row = conn.execute(
                        "SELECT token_id FROM registration_tokens WHERE token_string = ? AND is_active = 1",
                        (invite_token,)
                    ).fetchone()
                    if row:
                        is_beta_tester = True
            except:
                # Fallback for dev if table doesn't exist or other error
                is_beta_tester = invite_token.startswith("OMNI-BETA")
        
        # 1. Detect Language (Phase 28 enhancement)
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
        # 4. Handle Beta Tester Entry (Leadership Onboarding Protocol Step 1)
        final_greeting = lang_greetings.get(time_context, lang_greetings["morning"]) # Default fallback

        if is_beta_tester:
            beta_greetings = {
                LanguageCode.SPANISH: "¡Bienvenido al Protocolo de Liderazgo de OmniWeb! Has sido seleccionado para dar forma al futuro de este ecosistema. Soy tu Host IA, y te guiaré en tu camino de Tester a Administrador. ¿Listo para empezar?",
                LanguageCode.ENGLISH: "Welcome to the OmniWeb Leadership Protocol! You have been selected to shape the future of this ecosystem. I am your AI Host, and I will guide you from Tester to Administrator. Ready to begin?"
            }
            final_greeting = beta_greetings.get(user_lang, beta_greetings[LanguageCode.ENGLISH])
            
            # Log onboarding metrics (Protocol Step 3 Initial)
            try:
                from backend.core.database import db_manager
                with db_manager.get_connection() as conn:
                    # Update role to Beta Tester
                    conn.execute("UPDATE users SET role = 'beta_tester' WHERE id = ?", (user_id,))
                    
                    conn.execute("""
                        INSERT OR REPLACE INTO onboarding_analytics (user_id, step_reached, selected_language)
                        VALUES (?, ?, ?)
                    """, (user_id, 1, user_lang.value))
                    conn.commit()
            except:
                pass

        return {
            "detected_language": user_lang,
            "title": "Leadership Onboarding" if is_beta_tester else self.titles.get(user_lang, "Omni Shell"),
            "message": final_greeting,
            "time_context": time_context,
            "is_returning": is_returning,
            "is_beta": is_beta_tester,
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
