from typing import Dict, Any, Optional

class SessionState:
    def __init__(self):
        # Move state to a dictionary keyed by session_id
        self.session_data: Dict[str, Dict[str, Any]] = {}
        self._default_lang = "es"

    def _ensure_session(self, session_id: str):
        if session_id not in self.session_data:
            from .cognition.locale_manager import LocaleContext
            from backend.core.identity.space_registry import space_registry
            
            # Resolve stable Personal Space for this user/session
            space = space_registry.resolve_space(session_id)
            
            self.session_data[session_id] = {
                "locale": LocaleContext(ui_language=self._default_lang, response_language=self._default_lang),
                "space_id": space.space_id,
                "space_root": space.space_root
            }

    @property
    def language(self) -> str:
        """Legacy access for backward compatibility. Maps to 'default' session."""
        return self.get_language("default")

    @language.setter
    def language(self, value: str):
        """Legacy access for backward compatibility. Maps to 'default' session."""
        self.set_language("default", value)

    def get_language(self, session_id: str) -> str:
        self._ensure_session(session_id)
        return self.session_data[session_id]["locale"].ui_language

    def get_locale(self, session_id: str):
        """Returns the full rich locale context for a session."""
        self._ensure_session(session_id)
        return self.session_data[session_id]["locale"]

    def set_language(self, session_id: str, lang: str):
        self._ensure_session(session_id)
        locale = self.session_data[session_id]["locale"]
        
        # Normalize language input
        target_lang = self._default_lang
        if any(w in lang.lower() for w in ["español", "spanish", " es ", "es"]):
            target_lang = "es"
        elif any(w in lang.lower() for w in ["inglés", "english", " en ", "en"]):
            target_lang = "en"
        
        locale.ui_language = target_lang
        locale.response_language = target_lang # Sync response by default

    def get_space_root(self, session_id: str) -> str:
        """Returns the physical root path for the user's personal space."""
        self._ensure_session(session_id)
        return self.session_data[session_id]["space_root"]

    def get_space_id(self, session_id: str) -> str:
        """Returns the unique stable ID for the user's personal space."""
        self._ensure_session(session_id)
        return self.session_data[session_id]["space_id"]

# Persistent across the backend process, but data is segmented by session_id
session_state = SessionState()
