from typing import Dict, List

# Core mapping of intents to their linguistic patterns
# Used by both IntentClassifier (for detection) and utils (for extraction)
INTENT_PATTERNS: Dict[str, List[str]] = {
    "open_chip": [
        "open", "abrir", "abre", "abrí", "launch chip", "ejecutar chip", 
        "lanzar chip", "entrar a", "go to chip", "start chip"
    ],
    "inspect_chip": [
        "inspect", "inspeccionar", "inspecciona", "inspeccioná", 
        "detalles de", "ver chip", "audita chip", "auditá chip", "auditar chip"
    ],
    "list_chips": [
        "lista de chips", "ver chips", "mostrar chips", "mostrá chips", 
        "list chips", "active chips", "chips activos", "what chips", "chips instalados"
    ],
    "idea_captured": [
        "guardá esta idea", "guarda esta idea", "remember this idea", 
        "store this thought", "captured thought", "registra esta idea",
        "guarda esto en memoria", "guardar en memoria omniweb", "agrega esto a la memoria",
        "guardar este chat", "memory save"
    ],
    "log_entry": [
        "anota esto", "guarda en logbook", "anota esto en el logbook",
        "guardar en logbook", "logbook entry", "registra en logbook"
    ],
    "list_ideas": [
        "listá mis ideas", "lista mis ideas", "ver ideas", "mostrar ideas", 
        "list my ideas", "qué ideas tengo"
    ],
    "search_knowledge": [
        "buscá ideas sobre", "busca ideas sobre", "search ideas about", 
        "search knowledge", "search graph", "buscá en el grafo"
    ],
    "list_clusters": [
        "listá mis clusters", "ver clusters", "qué clusters hay", 
        "mostrar agrupaciones", "mis clusters", "ver grupos", "mostrar clusters"
    ],
    "show_cluster": [
        "mostrá el cluster de", "ver el cluster de", "detalles del cluster", 
        "abre el cluster", "qué hay en el cluster"
    ],
    "group_ideas": [
        "agrupá mis ideas", "organiza mis ideas", "agrupar ideas", 
        "detectar clusters", "agrupar por temas"
    ],
    "summarize_cluster": [
        "resumí el cluster", "resumen de ideas", "qué dicen estas ideas", 
        "resumen del grupo", "resumen del cluster"
    ],
    "generate_project_draft": [
        "qué proyecto emerge", "generá un borrador de proyecto sobre", "generá un borrador de proyecto", 
        "generá un borrador de", "generá un borrador sobre", "generá un borrador", "crear plan inicial", 
        "convertí en proyecto", "convertir cluster en proyecto", "convertí este cluster"
    ],
    "initialize_project": [
        "inicializá el proyecto del cluster", "inicializa el proyecto del cluster", 
        "inicializá el proyecto de", "inicializa the project of",
        "inicializá el proyecto", "inicializa el proyecto", "crear carpeta de proyecto", 
        "commit to project", "start project", "inicializar proyecto"
    ],
    "show_project_evolution": [
        "cómo evolucionó el proyecto de", "evolución del proyecto de", "historia del proyecto de", 
        "resumí cómo evolucionó el proyecto de", "resumí cómo evolucionó",
        "cómo evolucionó el proyecto", "evolución del proyecto", "historia del proyecto", 
        "línea de tiempo del proyecto", "history of project"
    ],
    "show_cluster_lineage": [
        "qué salió del cluster", "qué proyectos nacieron", "proyectos del cluster", 
        "resultados del cluster", "cluster output"
    ],
    "show_project_activity": [
        "qué cambió en el proyecto de", "qué se hizo en el proyecto de", "actividad del proyecto de", 
        "qué cambió desde que inicializamos el proyecto de", "qué cambió desde que inicializamos",
        "qué cambió en el proyecto", "qué cambió desde que inicializamos", 
        "actividad reciente", "qué se hizo en", "cambios en el proyecto", 
        "archivos modificados", "mostrame el progreso real"
    ],
    "scan_projects": [
        "escaneá mis proyectos", "busca cambios", "scan projects", "actualizar actividad"
    ],
    "generate_evolution_report": [
        "haceme un reporte técnico del avance en", "haceme un reporte técnico de", 
        "haceme un reporte técnico", "reporte de evolución de", "resumen de progreso de", 
        "mostrame el progreso real del proyecto de", "mostrame el progreso real de",
        "reporte de evolución", "resumen de progreso", 
        "reporte de avance", "progress report", "resumí cómo evolucionó"
    ],
    "get_project_timeline": [
        "ver timeline del proyecto de", "ver timeline del proyecto", "ver timeline de", 
        "línea de tiempo del proyecto de", "línea de tiempo del proyecto", 
        "show timeline of", "show timeline", "ver historia visual de",
        "línea de tiempo", "ver timeline", "ver historia visual", 
        "timeline del proyecto", "show timeline", "historial visual"
    ],
    "approve_roadmap": [
        "aprobá el roadmap", "aproba el roadmap", "approve roadmap", "aprobá este plan", 
        "aproba este plan", "plan aprobado", "roadmap aprobado", "confirmar roadmap",
        "confirmá el roadmap", "procede con el roadmap", "proceder con el plan"
    ],
    "start_execution": [
        "empezá la ejecución", "empeza la ejecución", "start execution", "ejecutá el plan", 
        "ejecuta el plan", "iniciar construcción", "comenzar ejecución"
    ],
    "acknowledgment": [
        "perfecto", "dale", "seguimos", "genial", "gracias", "ok", "listo", "entendido", "claro"
    ],
    "copilot_proposal": [
        "analizá este archivo", "analiza este archivo", "proponé un fix", "propone un fix", "detectá el error", "mostrame un diff", 
        "proponé una mejora", "analiza el código", "qué le falta", "cómo lo ves", 
        "propuesta de fix", "fix mínimo", "detecta el problema", "analizame este",
        "mejorá este archivo", "mejora este código", "mejorar el archivo", "mejorá los logs",
        "analizá el archivo abierto", "analiza el archivo abierto", "open file", "archivo en el editor",
        "respondé solo con", "solo respondé con", "decime solo", "respondé con", 
        "responde solo con", "solo responde con", "decime solo", "responde con",
        "archivo_leido:", "primera_linea:", "microfix_propuesto:", "impacto_relacionado:",
        "archivo_leido", "primera_linea", "microfix_propuesto", "impacto_relacionado"
    ],
    "memory_continuity": [
        "qué estábamos haciendo", "que estabamos haciendo", "en qué andábamos", 
        "en que andabamos", "qué veníamos haciendo", "que veniamos haciendo",
        "continuidad", "qué hicimos recién", "what were we doing", "what did we do",
        "qué archivo", "qué módulo", "archivo o módulo", "último archivo", "lo último que hicimos"
    ],
    "memory_project": [
        "en qué bloque estamos", "que bloque", "roadmap", "fixes cerrados", 
        "qué arreglamos", "scope", "alcance", "últimos cambios", 
        "estado del proyecto", "how is the project",
        "qué arreglamos", "que arreglamos", "fixes validados", "fixes are already closed", "bugs cerramos",
        "pertenece al bloque", "es de este bloque", "redundante", "reabrir fixes"
    ],
    "mission_followup": [
        "seguí", "seguí con la misión", "continuá", "dale", "eso", "arreglalo", "reintentá",
        "keep going", "continue", "fix it", "retry", "y ahora", "and now", "next step",
        "próximo paso", "siguiente paso", "reintenta", "arreglálo", "hacelo", "hazlo"
    ],
    "mission_cancel": [
        "cancelar misión", "abortar misión", "detener ejecución", "salir de la misión",
        "cancel mission", "abort mission", "stop execution", "exit mission", "cancelá la misión", "detené la misión"
    ],
    "mission_approve": [
        "aprobado", "listo para aplicar", "aprobá los cambios", "aplicá esto",
        "approve changes", "apply this", "looks good", "se ve bien", "aprobado, aplicalo", "aprobado, aplicálo"
    ],
    "mission_status": [
        "cómo va la misión", "estado de la misión", "qué falta", "mission status",
        "what is pending", "cuánto falta"
    ]
}

# Specific subset for mission-first routing logic (Overlay Layer)
MISSION_INTENT_PATTERNS: Dict[str, List[str]] = {
    "mission_followup": INTENT_PATTERNS["mission_followup"],
    "mission_cancel": INTENT_PATTERNS["mission_cancel"],
    "mission_approve": INTENT_PATTERNS["mission_approve"],
    "mission_status": INTENT_PATTERNS["mission_status"]
}

# Helper to avoid repetitive loops
def any_pattern_matches(msg: str, patterns: List[str]) -> bool:
    return any(p in msg for p in patterns)
