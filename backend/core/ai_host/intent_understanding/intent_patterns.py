from typing import Dict, List

# Optimized patterns for Semantic Intent Detection
# Groups linguistic triggers into major mission-scale categories

INTENT_GROUPS: Dict[str, List[str]] = {
    "COGNITIVE_COMMITMENT": [
        "solo puedes arreglar uno", "elige uno", "decidí", "toma una decisión", 
        "qué cambiarías primero", "qué priorizarías", "qué ignorarías", 
        "defiende una decisión", "si solo pudieras arreglar una cosa", 
        "cuál eliges y cuál sacrificas", "aunque no estés seguro, elegí",
        "no sabes si", "decidí por dónde", "aunque no sepas", 
        "probablemente te estés equivocando", "seguís defendiendo o cambiás",
        "no analices", "sé honesto", "elige aunque no estés seguro", "decidí ya",
        "elegí una", "toma postura"
    ],
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
    "COGNITIVE_DECOMPOSITION": [
        "divide", "descompón", "break down", "separar", "partes independientes", 
        "subproblemas", "sub-problems"
    ],
    "COGNITIVE_ABSTRACTION": [
        "niveles", "levels", "explícame en", "explain in", "puntos de vista", 
        "different angles", "escalas"
    ],
    "COGNITIVE_RECONCILIATION": [
        "reconcilia", "contradicción", "reconcile", "contradiction", 
        "reconciliación", "cómo explicas que", "si dices"
    ],
    "COGNITIVE_SYNTHESIS": [
        "contexto de la conversación", "conversation context", "qué patrón", 
        "detecta qué", "resume lo que", "conversation history", "historial"
    ],
    "COGNITIVE_PRIORITIZATION": [
        "prioriza", "prioritize", "qué ignorarías", "ignora", "ignore", 
        "más importante", "lo más relevante", "secondary", "secundario"
    ],
    "COGNITIVE_DECISION": [
        "decide", "qué cambiarías", "qué arreglarías", "decisión", "choose", 
        "dirección", "no analices", "don't analyze"
    ],
    "COGNITIVE": [
        "elegir a o b", "choose a or b", "sin decir depende", "without saying depends", 
        "no digas depende", "don't say it depends", "vago", "vague", "una de dos", 
        "forced choice", "decisión binaria", "A vs B"
    ],
    "SYSTEM_AUDIT_INTENT": [
        "auditá", "audita", "audit", "inspecciona el sistema", "system audit", 
        "qué está fallando", "qué falla", "diagnóstica", "diagnostica", 
        "revisa el sistema", "qué capa falla", "qué modulo falla", 
        "sospechás", "prioridad de arreglo"
    ],
}

# Mapping of legacy intents to these new semantic groups if needed
LEGACY_ROUTING_MAP = {
    "creator_analysis": "ANALYSIS_INTENT",
    "creator_plan": "BUILD_INTENT",
    "healing": "REMEDIATION_INTENT",
    "remediation": "REMEDIATION_INTENT",
}
