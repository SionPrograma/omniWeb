import re

class LanguageIntentDetector:
    def detect_intent(self, msg_clean: str) -> dict:
        words = msg_clean.split()
        
        # Intent Flags
        is_mixed = ("hello" in msg_clean or "hi " in msg_clean or "english" in msg_clean) and \
                   ("hola" in msg_clean or "español" in msg_clean or "bien" in msg_clean)
        
        is_short = "corto" in msg_clean or "breve" in msg_clean or "short" in msg_clean
        is_detailed = "largo" in msg_clean or "detalle" in msg_clean or "detailed" in msg_clean or "explica bien" in msg_clean
        
        intent_type = "unknown"
        extracted_text = None
        
        if is_mixed:
            intent_type = "spanglish_conversation"
            
        elif re.search(r"(?:traduce|traducir|translate|cómo se dice|como se dice)\s*(.*)", msg_clean):
            intent_type = "translation"
            m = re.search(r"(?:traduce|traducir|translate|cómo se dice|como se dice)\s*(.*)", msg_clean)
            extracted_text = m.group(1).strip() if m and m.group(1).strip() else "el texto"
            if len(extracted_text) < 3: extracted_text = "el texto"
            
        elif "corrige" in msg_clean or "corregir" in msg_clean or "está bien escrito" in msg_clean or "reformular" in msg_clean:
            intent_type = "correction"
            
        elif "resumen" in msg_clean or "resume" in msg_clean or "summary" in msg_clean or "sintetizar" in msg_clean:
            intent_type = "summary"
            
        elif "omniweb" in msg_clean or "omniword" in msg_clean or "quién eres" in msg_clean or ("explica" in msg_clean and "omni" in msg_clean):
            intent_type = "explanation"
            
        else:
            greetings = ["hola", "hello", "buenas", "hi ", "hey "]
            if any(msg_clean.startswith(g) for g in greetings) or (len(words) <= 3 and any(g in msg_clean for g in ["hola", "hello", "buenas", "hi", "hey"])):
                intent_type = "greeting"
            elif len(words) > 3 and "?" in msg_clean:
                intent_type = "question"
            elif "habla" in msg_clean or "cualquier cosa" in msg_clean or "cuéntame" in msg_clean:
                intent_type = "smalltalk"

        return {
            "type": intent_type,
            "is_short": is_short,
            "is_detailed": is_detailed,
            "extracted_text": extracted_text,
            "raw_msg": msg_clean
        }
