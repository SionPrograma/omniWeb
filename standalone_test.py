import re
import random

class MockSession:
    def __init__(self):
        self.language = "es"

session_state = MockSession()

class CognitiveOrchestrator:
    FORBIDDEN_LABELS = [
        "OBSERVATION", "OBSERVACIÓN", "ANALYSIS", "ANÁLISIS", "PLAN", "MISSION", "MISIÓN",
        "HYPOTHESIS PRIMARIA", "HIPÓTESIS PRIMARIA", "HYPOTHESIS", "HIPÓTESIS",
        "ALTERNATIVE EXPLANATION", "EXPLICACIÓN ALTERNATIVA", "EVIDENCE", "EVIDENCIA",
        "CONFIDENCE LEVEL", "NIVEL DE CONFIANZA", "MISSING EVIDENCE", "EVIDENCIA FALTANTE",
        "RECOMMENDED ACTION", "ACCIÓN RECOMENDADA", "RECOMMENDED NEXT STEP",
        "RELIABILITY", "CONFIABILIDAD", "LEARNING", "APRENDIZAJE", "PATCH", "PARCHE", 
        "CONTEXTO COGNITIVO", "TECHNICAL REASONING", "SYSTEM STATUS", "PRIMARIA", "SECUNDARIA",
        "TO", "FROM", "ORIGINAL", "TRANSLATED", "CONFIRMATION", "YOUR CONTACTS", "CONTACTS",
        "MESSAGE", "ORIGINAL TEXT", "TARGET LANGUAGE", "STATUS", "RECIPIENT",
        "INFORME DE SALUD", "SALUD DEL SISTEMA", "SOLUCIONES DE AUTOCURACIÓN", "ACCIONES DE AUTOCURACIÓN",
        "CONFIRMACIÓN DE AUTOCURACIÓN", "AUTOCURACIÓN COMPLETADA", "REPARACIÓN", "SOLUCIÓN DISPONIBLE",
        "HEALTH REPORT", "SYSTEM HEALTH", "SELF-HEALING SOLUTIONS", "HEALING ACTIONS",
        "CONFIRMATION REQUIRED", "HEALING COMPLETED", "REPAIR", "SOLUTION AVAILABLE",
        "REPORTE DE DIAGNÓSTICO TÉCNICO", "TECHNICAL DIAGNOSTIC REPORT", "REPORTE DE DIAGNÓSTICO",
        "DIAGNOSTIC REPORT", "PATCH PREVIEW", "VISTA PREVIA DEL PARCHE", "PATCH GENERATED",
        "MISSION CONTROL", "COMANDO RECIBIDO", "COMMAND RECEIVED", "SYSTEM REQUEST", "EXECUTION STATUS", "ESTADO DE EJECUCIÓN",
        "PLAN INTEGRADO", "INTEGRATED PLAN", "VERIFICACIÓN", "VERIFY", "RESULTADO", "OUTCOME", "MISIÓN DISPUESTA", "MISSION DISPATCHED"
    ]

    def _naturalize(self, text: str) -> str:
        lang = session_state.language
        text = re.sub(r'[\U00010000-\U0010ffff\u2600-\u26ff\u2700-\u27bf]', '', text)
        text = re.sub(r'#+\s+', '', text)
        text = re.sub(r'\*\*(.*?)\*\*', r'\1', text)
        text = re.sub(r'\_\_(.*?)\_\_', r'\1', text)
        
        jargon_patterns = [
            (r'(?i)the system is currently in (\w+) state', {"es": "todo parece estar en orden", "en": "everything seems to be in order"}),
            (r'(?i)system status is (\w+)', {"es": r"el estado general es \1", "en": r"the overall status is \1"}),
            (r'(?i)metrical noise or ntp drift', {"es": "unas ligeras fluctuaciones técnicas", "en": "slight technical fluctuations"}),
            (r'(?i)nominal|healthy', {"es": "bien", "en": "fine"}),
            (r'(?i)primary anomaly detected in ([\w\._/]+)', {"es": r"he notado algo extraño en \1 que no me termina de encajar", "en": r"I've noticed something odd in \1 that doesn't quite fit"}),
            (r'(?i)detected performance degradation (in|at) ([\w\s_\-/]+)', {"es": r"parece que el rendimiento de \2 ha bajado un poco", "en": r"it seems that \2 has dipped in performance"}),
            (r'(?i)detected performance degradation', {"es": "parece que el rendimiento ha bajado un poco", "en": "it seems performance has dipped a bit"}),
            (r'(?i)latency issue', {"es": "un posible retraso en la comunicación", "en": "a possible communication delay"}),
            (r'(?i)with (\d+) active (chips|modules)', {"es": r"con \1 módulos operando", "en": r"with \1 modules running"}),
            (r'(?i)all processes are stable', {"es": "todo está bajo control", "en": "everything is under control"}),
            (r'(?i)background tasks', {"es": "tareas en segundo plano", "en": "background tasks"}),
            (r'(?i)executing (\w+) tasks', {"es": r"trabajando en tareas de \1", "en": r"working on \1 tasks"}),
            (r'(?i)initiate creator for ([\w\s_\-/]+)', {"es": r"voy a activar el modo de creación para revisar \1", "en": r"I'll start creator mode to check \1"}),
            (r'(?i)no results found for ([\w\s_\-/]+)', {"es": r"no he podido encontrar nada sobre \1", "en": r"I couldn't find anything about \1"}),
            (r'(?i)search completed', {"es": "ya terminé la búsqueda", "en": "I'm done with the search"}),
        ]

        for pattern, replacement_map in jargon_patterns:
            repl = replacement_map.get(lang, replacement_map.get("en", ""))
            text = re.sub(pattern, repl, text)

        raw_lines = text.split('\n')
        processed_sentences = []
        label_pattern = "|".join(sorted(self.FORBIDDEN_LABELS, key=len, reverse=True))
        connectors = {
            "es": ["por lo que veo,", "parece que,", "probablemente,", "lo más lógico es que,", "la verdad es que,", "estoy viendo que,"],
            "en": ["from what I see,", "it looks like,", "probably,", "it stands to reason that,", "to be honest,", "I'm seeing that,"]
        }
        
        for line in raw_lines:
            line = line.strip()
            if not line: continue
            clean_line = re.sub(rf'(?i)\b({label_pattern})\b[\s\-:]*', '', line)
            clean_line = re.sub(r'^[\-\*\•\d\.\)]+\s*', '', clean_line)
            clean_line = clean_line.strip(' :-•·')
            if not clean_line: continue

            if lang == "es":
                translations = {
                    r'\bin ': 'en ', r'\bon ': 'en ', r'\bwith ': 'con ', r'\band ': 'y ',
                    r'\bsuccess\b': 'éxito', r'\berror\b': 'problema', r'\bnone\b': 'ninguno',
                    r'\bactive\b': 'activos', r'\bidle\b': 'en espera', r'\btask\b': 'tarea',
                    r'\btasks\b': 'tareas', r'\bsuccessfully\b': 'correctamente',
                    r'\bbackground\b': 'segundo plano'
                }
                for eng, esp in translations.items():
                    clean_line = re.sub(eng, esp, clean_line, flags=re.IGNORECASE)

            if len(processed_sentences) == 0 and len(clean_line) > 15:
                conn = connectors[lang][0] 
                if not any(clean_line.lower().startswith(c.split(',')[0]) for c in connectors[lang]):
                    clean_line = f"{conn} {clean_line[0].lower() + clean_line[1:]}"
            if len(clean_line) > 1:
                clean_line = clean_line[0].upper() + clean_line[1:]
            if clean_line and not clean_line[-1] in ['.', '!', '?', ';']:
                clean_line += '.'
            if clean_line:
                processed_sentences.append(clean_line)

        if not processed_sentences:
            return "Lo tengo. He revisado todo y parece estar en orden." if lang == "es" else "Got it. I've checked everything and it looks good."

        unified_flow = " ".join(processed_sentences)
        unified_flow = re.sub(r'\s{2,}', ' ', unified_flow)
        unified_flow = re.sub(r'\.\s*\.', '.', unified_flow)
        unified_flow = re.sub(r'[\.\,]{2,}', '.', unified_flow)
        return unified_flow.strip()

orch = CognitiveOrchestrator()
tests = [
    "The system is currently in HEALTHY state with 0 active chips. Primary anomaly detected in flow.ai_to_chips.latency.",
    "OBSERVATION: Detected performance degradation in background tasks. Hypothesis: Metrical noise or NTP drift.",
    "System status is nominal. Success in executing background tasks."
]

for t in tests:
    print(f"Input: {t}")
    print(f"Output: {orch._naturalize(t)}")
    print("-" * 20)
