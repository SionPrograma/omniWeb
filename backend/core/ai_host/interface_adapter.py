from enum import Enum
from typing import Optional

class InterfaceMode(Enum):
    TEXT = "text"
    VOICE = "voice"
    HOLOGRAPHIC = "holographic"

class InterfaceAdapter:
    """
    Abstraction layer for different AI Host interfaces.
    """
    def __init__(self, mode: InterfaceMode = InterfaceMode.TEXT):
        self.mode = mode

    def _normalize_for_speech(self, text: str) -> str:
        """
        Transforms markdown and technical patterns into natural human speech.
        """
        import re
        if not text:
            return ""

        # 1. Global strip of dangerous speech markers (escapes, backticks, emphasis)
        text = text.replace('`', ' ') # Backticks cause some TTS to say "accent"
        text = text.replace('**', '') # Bold
        text = text.replace('__', '') # Bold
        text = text.replace('*', '')  # Emphasis / Bullet residuals
        
        # 2. Markdown syntax residuals
        text = re.sub(r'#+\s+', '', text)               # Headers #
        text = re.sub(r'[-]\s+', ' ', text)             # Bullets at start

        # 2. Normalize technical paths (backend/core/...)
        def path_replacer(match):
            path = match.group(0)
            # Remove extension
            path = re.sub(r'\.(py|js|ts|css|html|md|json)$', '', path)
            # Replace separators with humans words
            parts = re.split(r'[\\/]', path)
            if len(parts) > 2:
                # Summarize deep paths: "backend/core/ai_host" -> "módulo ai host del backend"
                return f"el módulo {parts[-1].replace('_', ' ')} de {parts[0]}"
            return " de ".join(reversed([p.replace('_', ' ') for p in parts]))

        # 3. Normalize technical paths (backend/core/...)
        # Broaden regex to catch paths even without word boundaries if surrounded by symbols
        text = re.sub(r'[\w\-\.\\]+[\\/][\w\-\.\\/]+', path_replacer, text)
        
        # 4. Phonetic & Entity Protection (Phase 10 Fine-Grained)
        # Prevent "shell" -> "ser" or other mispronunciations in specific contexts
        protections = {
            r"\bshell\b": "shell", # Guard against any transformation to "ser"
            r"\bai host\b": "ai host",
            r"\bproposal\b": "proposal"
        }
        for pattern, replacement in protections.items():
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE)

        # 5. Handle standalone filenames and remaining extensions
        # Match filenames like "main.py" or "config.json"
        text = re.sub(r'\b([\w\-]+)\.(py|js|ts|css|html|md|json)\b', r'\1', text)

        # 6. Clean up remaining underscores and miscellaneous symbols
        text = text.replace('_', ' ')
        text = text.replace('*', '')  # Just in case
        
        # 7. Filter common emojis/decorative symbols for cleaner speech
        text = re.sub(r'[⚠️✓📄⚛️✨🤖🔍]', '', text)
        
        text = re.sub(r'\s+', ' ', text) # Collapse spaces

        return text.strip()

    def format_response(self, text: str, data: Optional[dict] = None) -> dict:
        """
        Adapts the response based on the current mode and adds multimodal logic.
        """
        response = {
            "mode": self.mode.value,
            "message": text,
            "speech": self._normalize_for_speech(text), # Always provide normalized speech
            "payload": data or {}
        }
        
        # Multimodal Layer: Visual response generation (Phase J)
        if data and "visual" in data:
             response["visual"] = data["visual"]
        
        if self.mode == InterfaceMode.TEXT:
            response["display_data"] = data or {}
        elif self.mode == InterfaceMode.VOICE:
            # For voice mode, we might want to prioritize speech but keep message for UI
            pass
            
        return response

adapter = InterfaceAdapter(InterfaceMode.TEXT)
