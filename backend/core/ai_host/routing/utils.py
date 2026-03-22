import re
from typing import Optional
from .patterns import INTENT_PATTERNS

def extract_chip_target(msg: str) -> str:
    """
    Isolates the main chip/entity name from a technical query.
    """
    if not msg: return ""
    clean = msg.lower().strip()
    
    # 1. Removal of technical filler/predicates
    noise_predicates = [
        "no se ve", "no responde", "falla", "anda mal", "anda raro",
        "no se ve bien", "no está viendo", "no se esta viendo",
        "no carga", "error en", "problema en", "bug en", "se rompió"
    ]
    for p in noise_predicates:
        clean = clean.replace(p, " ")

    # 2. Extract specific chip names if preceded by "chip"
    chip_match = re.search(r"chip\s+([a-z0-9_-]+)", clean)
    if chip_match:
        return chip_match.group(1).strip()
        
    # 3. Fallback: use basic isolation logic
    noise_words = ["el", "la", "un", "una", "de", "del", "en", "mapa", "botón", "interfaz"]
    words = [w for w in clean.split() if w not in noise_words and len(w) > 2]
    
    return words[0] if words else "sistema"

def extract_component_from_target(msg: str) -> Optional[str]:
    """Extracts a subcomponent like 'mapa', 'botón', 'listado' if mentioned."""
    low = msg.lower()
    if "mapa" in low: return "mapa"
    if "botón" in low or "boton" in low: return "botón"
    if "lista" in low: return "listado"
    if "selector" in low: return "selector"
    return None

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
