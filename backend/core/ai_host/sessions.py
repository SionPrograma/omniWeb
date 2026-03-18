from typing import Dict, Any, Optional

class SessionState:
    def __init__(self):
        # Move state to a dictionary keyed by session_id
        self.session_data: Dict[str, Dict[str, Any]] = {}

    def _ensure_session(self, session_id: str):
        if session_id not in self.session_data:
            self.session_data[session_id] = {
                "language": "es"
            }

    def get_language(self, session_id: str) -> str:
        self._ensure_session(session_id)
        return self.session_data[session_id]["language"]

    def set_language(self, session_id: str, lang: str):
        self._ensure_session(session_id)
        if any(w in lang.lower() for w in ["español", "spanish", " es ", "es"]):
            self.session_data[session_id]["language"] = "es"
        elif any(w in lang.lower() for w in ["inglés", "english", " en ", "en"]):
            self.session_data[session_id]["language"] = "en"

# Persistent across the backend process, but data is segmented by session_id
session_state = SessionState()
