from typing import Dict, List

# Optimized patterns for Semantic Intent Detection
# Groups linguistic triggers into major mission-scale categories

INTENT_GROUPS: Dict[str, List[str]] = {
    "BUILD_INTENT": [
        "crea", "desarrolla", "build", "create", "implement", "evolve", 
        "evoluciona", "inicia", "desarrollo", "constructor", "builder"
    ],
    "ANALYSIS_INTENT": [
        "qué está mal", "what is wrong", "qué pasa", "what's wrong", 
        "analiza", "analyze", "explica", "explain", "diagnóstico", "diagnostic",
        "por qué", "why", "cómo funciona", "how it works", "improve", "mejora",
        "sugiere", "suggest", "qué sigue", "what next"
    ],
    "REMEDIATION_INTENT": [
        "cómo arreglarías", "how would you fix", "soluciona", "solve", 
        "repara", "heal", "fix", "corrige", "correct", "propón solución", "propose solution"
    ],
    "FOLLOW_UP_INTENT": [
        "y ahora", "and now", "seguimos", "keep going", "siguiente paso", 
        "next step", "dale", "continuemos", "go on", "what next", "continuar"
    ],
    "EXPLORATION_INTENT": [
        "muéstrame", "show me", "explora", "explore", "inspecciona", 
        "inspect", "ver detalles", "view details", "qué hay de"
    ],
    "VOICE_COMMAND_INTENT": [
        "hazlo", "do it", "vale", "ok", "listo", "perfecto", "claro", 
        "sí", "no", "cancela", "stop"
    ],
}

# Mapping of legacy intents to these new semantic groups if needed
LEGACY_ROUTING_MAP = {
    "creator_analysis": "ANALYSIS_INTENT",
    "creator_plan": "BUILD_INTENT",
    "healing": "REMEDIATION_INTENT",
    "remediation": "REMEDIATION_INTENT",
}
