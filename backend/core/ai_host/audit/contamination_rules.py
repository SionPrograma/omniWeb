import re
from typing import List, Dict, Any

# Evasion patterns (Spanish and English)
EVASION_PATTERNS = [
    r"depende", r"parece", r"hay algo", r"me da la sensación", 
    r"creo que", r"no termina de encajar", r"voy a mirar", 
    r"me voy a centrar", r"dale para adelante", r"chequeá el flujo",
    r"it depends", r"it seems", r"something feels off", r"I can't quite",
    r"I'll look into it", r"I'm going to look", r"maybe", r"probably",
    r"not sure", r"something weird", r"something is wrong"
]

# Cognitive signal patterns (Positive)
COGNITIVE_SIGNALS_ES = [r"decido", r"elijo", r"apuesto", r"razón", r"descarto", r"sacrifico", r"diagnóstico", r"acción"]
COGNITIVE_SIGNALS_EN = [r"decide", r"choose", r"bet", r"reason", r"discard", r"sacrifice", r"diagnostic", r"action"]

# Language detection (Simplified for V1)
SPANISH_KEYWORDS = ["el", "la", "que", "con", "para", "por", "si", "no", "es", "en", "lo", "un", "una", "de", "del", "pero", "y", "está", "esta", "como"]
ENGLISH_KEYWORDS = ["the", "and", "that", "with", "for", "if", "not", "is", "in", "to", "it", "as", "at", "be", "this", "on", "a", "an", "but", "so"]

def check_evasion(text: str) -> List[str]:
    found = []
    for pattern in EVASION_PATTERNS:
        if re.search(rf"(?i)\b{pattern}\b", text):
            found.append(pattern)
    return found

def detect_mixed_language(text: str) -> bool:
    # Very simple heuristic: count typical small words
    words = text.lower().split()
    es_count = sum(1 for w in words if w in SPANISH_KEYWORDS)
    en_count = sum(1 for w in words if w in ENGLISH_KEYWORDS)
    
    # If both are significant, it's mixed
    total_markers = es_count + en_count
    if total_markers < 3: return False
    
    # Check if the minority language has at least 20% presence
    minority = min(es_count, en_count)
    majority = max(es_count, en_count)
    
    ratio = minority / majority if majority > 0 else 0
    return ratio > 0.2 and minority >= 1

def check_cognitive_contract(text: str, lang: str = "es") -> Dict[str, bool]:
    patterns = COGNITIVE_SIGNALS_ES if lang == "es" else COGNITIVE_SIGNALS_EN
    
    # Check for core components
    has_decision = any(re.search(rf"(?i)\b{p}\b", text) for p in patterns[:3]) # decido, elijo, apuesto
    has_reason = any(re.search(rf"(?i)\b{p}\b", text) for p in patterns[3:4]) # razón
    has_discard = any(re.search(rf"(?i)\b{p}\b", text) for p in patterns[4:6]) # descartó, sacrifico
    
    # Alternative technical components
    has_diagnostic = any(re.search(rf"(?i)\b{p}\b", text) for p in patterns[6:7])
    has_action = any(re.search(rf"(?i)\b{p}\b", text) for p in patterns[7:8])
    
    return {
        "has_decision": has_decision,
        "has_reason": has_reason,
        "has_discard": has_discard,
        "has_diagnostic": has_diagnostic,
        "has_action": has_action
    }

def detect_narrative_residue(text: str) -> bool:
    # Check if a technical-looking block is followed by conversational filler
    # Example: "Config: {...} \n\n Bueno, ya está, avisame."
    residue_patterns = [
        r"avisame", r"estoy listo", r"qué más", r"dime si",
        r"let me know", r"I'm ready", r"next phase", r"how can I help"
    ]
    lines = text.split('\n')
    if len(lines) < 2: return False
    
    last_block = "\n".join(lines[-3:]) # Last 3 lines
    return any(re.search(rf"(?i)\b{p}\b", last_block) for p in residue_patterns)
