import requests
from ..models.lingua_config import settings
from deep_translator import GoogleTranslator

class Translator:
    def __init__(self):
        self.url = f"{settings.LIBRETRANSLATE_URL}/translate"

    def translate(self, text: str, target_lang: str) -> str:
        # If target language matches source conceptually, or text is empty, just return text
        if not text or not text.strip():
            return text

        # Step 1: Try LibreTranslate
        try:
            response = requests.post(
                self.url, 
                json={
                    "q": text,
                    "source": "auto",
                    "target": target_lang,
                    "format": "text"
                },
                timeout=5 # Add timeout to avoid hanging
            )
            response.raise_for_status()
            translated = response.json().get("translatedText")
            if translated and isinstance(translated, str) and translated.strip():
                return translated
        except Exception as e:
            print(f"[Translator] LibreTranslate failed ({type(e).__name__}): {e}. Falling back to Google Translate...")
            
        # Step 2: Fallback to Google Translate (via deep-translator)
        try:
            # deep-translator handles languages slightly differently, 
            # but usually 'es', 'en', etc. are standard.
            translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
            if translated and isinstance(translated, str) and translated.strip():
                return translated
        except Exception as ge:
            print(f"[Translator] Google Translate failed ({type(ge).__name__}): {ge}. Returning original text.")
            
        # Step 3: Ultimate fallback - return original text
        print(f"[Translator] All translation services failed for chunk: {text[:30]}... using original text fallback.")
        return text
