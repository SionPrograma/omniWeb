import os
import json
import logging
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class LocaleContext(BaseModel):
    """
    V1.0 Block 01: Rich Locale Context.
    Tracks language, formatting, timezone, and regional preferences.
    """
    ui_language: str = "es"
    response_language: str = "es"
    locale_code: str = "es-ES"
    timezone: str = "UTC"
    region: str = "EU"
    fallback_language: str = "en"
    coverage: float = 1.0

class LocaleManager:
    """
    Centralized I18N manager for OmniWeb.
    Loads dictionaries and resolves translation keys with fallback.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LocaleManager, cls).__new__(cls)
            cls._instance._dictionaries: Dict[str, Dict[str, Any]] = {}
            cls._instance._load_all_dictionaries()
        return cls._instance

    def _load_all_dictionaries(self):
        """Loads all .json files from the translations directory."""
        self._dictionaries = {} # Clear before load
        base_path = os.path.join(os.path.dirname(__file__), "translations")
        if not os.path.exists(base_path):
            os.makedirs(base_path, exist_ok=True)
            logger.warning(f"[LOCALE_MANAGER] Created missing translations directory: {base_path}")
            return
 
        for filename in sorted(os.listdir(base_path)): # Sorted for deterministic load
            if filename.startswith("strings.") and filename.endswith(".json"):
                lang = filename.split(".")[1]
                try:
                    with open(os.path.join(base_path, filename), "r", encoding="utf-8") as f:
                        self._dictionaries[lang] = json.load(f)
                        logger.info(f"[LOCALE_MANAGER] Loaded dictionary: {lang}")
                except Exception as e:
                    logger.error(f"[LOCALE_MANAGER] Failed to load dictionary {filename}: {e}")
 
    def reload_dictionaries(self):
        """Public trigger to refresh translations from disk."""
        logger.info("[LOCALE_MANAGER] Manually reloading all dictionaries.")
        self._load_all_dictionaries()

    def get_text(self, key: str, lang: str = "es", **kwargs) -> str:
        """
        Resolves a translation key with fallback logic.
        Key example: 'shell.nav.home'
        """
        keys = key.split(".")
        
        # 1. Try Target Language
        val = self._resolve_key_path(self._dictionaries.get(lang, {}), keys)
        if val is not None:
            return self._format(val, **kwargs)

        # 2. Try Fallback Language (en)
        val = self._resolve_key_path(self._dictionaries.get("en", {}), keys)
        if val is not None:
            return self._format(val, **kwargs)

        # 3. Honest Failure
        logger.warning(f"[LOCALE_MANAGER] Missing translation key: {key} for lang: {lang}")
        return f"[MISSING: {key}]"

    def _resolve_key_path(self, dictionary: Dict, keys: list) -> Optional[str]:
        current = dictionary
        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return None
        return str(current) if isinstance(current, (str, int, float)) else None

    def _format(self, text: str, **kwargs) -> str:
        if not kwargs: return text
        try:
            return text.format(**kwargs)
        except Exception as e:
            logger.warning(f"[LOCALE_MANAGER] Format error for '{text[:20]}...': {e}")
            return text

# Singleton Instance
locale_manager = LocaleManager()
