from typing import Dict, Any, Optional

class SessionState:
    def __init__(self):
        self.language = "es" # Default to Spanish per project preference

    def set_language(self, lang: str):
        if "español" in lang.lower() or "spanish" in lang.lower() or " es " in f" {lang.lower()} " or lang.lower() == "es":
            self.language = "es"
        elif "inglés" in lang.lower() or "english" in lang.lower() or " en " in f" {lang.lower()} " or lang.lower() == "en":
            self.language = "en"

# Singleton across the backend process
session_state = SessionState()
