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
    ]
}

# Helper to avoid repetitive loops
def any_pattern_matches(msg: str, patterns: List[str]) -> bool:
    return any(p in msg for p in patterns)
