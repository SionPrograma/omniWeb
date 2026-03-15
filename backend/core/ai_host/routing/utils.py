import re
from .patterns import INTENT_PATTERNS

def extract_chip_target(msg: str) -> str:
    """
    Robustly extracts a chip target from a natural language command.
    Removes prefixes, verbs, and common connector words.
    """
    if not msg:
        return ""

    # 1. Basic normalization
    clean = msg.lower().strip()
    
    # Remove leading/trailing punctuation and common filler
    clean = re.sub(r'^[¡¿!?,. ]+', '', clean)
    clean = re.sub(r'[!?,. ]+$', '', clean)
    
    # 2. Strip Creator Prefixes
    prefixes = ["omni", "system", "host", "ia", "ai", "creator"]
    for p in prefixes:
        # Match as word to avoid partial matches
        pattern = rf'^{p}\b[,. ]*'
        clean = re.sub(pattern, '', clean).strip()

    # 3. Multi-word Phrases (Priority: Longest first)
    # Combine patterns from open_chip and inspect_chip
    core_noise = INTENT_PATTERNS["open_chip"] + INTENT_PATTERNS["inspect_chip"]
    noise_phrases = sorted(core_noise, key=len, reverse=True)
    
    # Add articles and connectors
    noise_phrases += [
        "el chip", "la chip", "un chip", "the chip", "my chip",
        "por favor", "please", "dame", "ver el", "el ", "la ", "the "
    ]
    
    for phrase in noise_phrases:
        clean = clean.replace(phrase, " ")

    # 4. Single-word Verbs and Noise
    noise_words = [
        "abre", "abrí", "open", "launch", "ejecutar", "lanzar", "chip",
        "inspecciona", "inspeccioná", "inspeccionar", "auditá", "audita", "auditar",
        "ver", "acceder", "start", "run", "inicia", "iniciá", "mostrá", "mostrar", "lista",
        "el", "la", "los", "las", "the", "a", "an", "de", "con", "en", "qué", "que"
    ]
    
    # Split into words and filter
    words = clean.split()
    filtered_words = [w for w in words if w not in noise_words]
    
    final_target = " ".join(filtered_words).strip()
    
    return final_target

def _strip_host_prefixes(msg: str) -> str:
    """Helper to remove Omni/System/Host prefixes."""
    clean = msg.lower().strip()
    prefixes = ["omni", "system", "host", "ia", "ai", "creator"]
    for p in prefixes:
        pattern = rf'^{p}\b[,. ]*'
        clean = re.sub(pattern, '', clean).strip()
    return clean

def extract_idea_content(msg: str) -> str:
    """
    Strips 'guardá esta idea:', 'remember this:', etc. to isolate the core thought.
    """
    clean = _strip_host_prefixes(msg)
    
    # Remove common patterns
    patterns = INTENT_PATTERNS["idea_captured"] + ["guardá", "guarda", "remember", "anota", "registra"]
    
    for p in patterns:
        pattern = rf'^{p}[: ]*'
        clean = re.sub(pattern, '', clean).strip()
        
    # Remove leading/trailing punctuation or quotes
    clean = re.sub(r'^[¡¿!?,. : "\' ]+', '', clean)
    clean = re.sub(r'[!?,. : "\' ]+$', '', clean)
    
    return clean

def extract_memory_query(msg: str) -> str:
    """
    Isolates the search term from memory intents.
    """
    clean = _strip_host_prefixes(msg)
    
    # Aggregate all relevant patterns for extraction
    all_memory_patterns = []
    for intent in [
        "search_knowledge", "show_cluster", "summarize_cluster", 
        "generate_project_draft", "initialize_project", 
        "show_project_evolution", "show_project_activity",
        "generate_evolution_report", "get_project_timeline"
    ]:
        all_memory_patterns.extend(INTENT_PATTERNS.get(intent, []))
        
    # Add common noise verbs
    all_memory_patterns += ["buscá", "busca", "search", "busque", "encuentra", "find", "ver", "mostrá", "resumí"]
    
    # Sort by length to avoid partial matches (e.g. 'resumí' before 'resumí el cluster')
    all_memory_patterns = sorted(all_memory_patterns, key=len, reverse=True)
    
    for p in all_memory_patterns:
        pattern = rf'^{p}[: ]*'
        clean = re.sub(pattern, '', clean).strip()
        
    # Remove bridge words: 'de', 'del', 'sobre', 'el', 'la', 'un', 'una', 'el cluster', 'del cluster'
    clean = re.sub(r'^(de|del|sobre|el|la|un|una|the|of|about|el cluster|del cluster|cluster)\s+', '', clean, flags=re.IGNORECASE)
    
    # Final trim
    clean = re.sub(r'^[¡¿!?,. : "\' ]+', '', clean)
    clean = re.sub(r'[!?,. : "\' ]+$', '', clean)
    
    return clean
