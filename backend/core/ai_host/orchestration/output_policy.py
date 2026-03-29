import re
from dataclasses import dataclass

@dataclass
class OutputPolicy:
    """
    Unified Output Constraints Policy for OmniWeb.
    Phase 1 of Architectural Reassembly.
    Ensures that all orchestrators follow the same response guidelines.
    """
    show_telemetry: bool = True
    show_header: bool = True
    show_action: bool = True
    show_footer: bool = True
    is_minimal: bool = False
    is_brief: bool = False
    is_report_mode: bool = True
    suppress_audit: bool = False
    suppress_block: bool = False
    suppress_runtime: bool = False
    tone: str = "executive" # "executive" | "natural"

    @classmethod
    def from_query(cls, query: str):
        low = query.lower()
        
        # 1. Detection of Minimal/Brief constraints
        is_minimal = any(k in low for k in ["solo", "only", "nada más", "nada mas", "frase corta", "una frase", "en una frase", "en una sola frase", "mínima", "minima", "sin rellenar", "limpio", "únicamente", "unicamente"])
        is_brief = is_minimal or any(k in low for k in ["rápido", "rapido", "quick", "resumen", "resumí", "resumi", "breve", "acotado"])
        
        # 2. Hard Suppression Markers
        negations = ["no me digas", "no menciones", "no repitas", "no agregues", "no incluyas", "sin decir", "sin leer", "sin mencionar", "sin incluir", "omite", "omití", "no me hagas", "no cambies", "sin reporte", "no reportes", "no reporte", "sin dump", "sin irte"]
        
        # 3. Specific Flags
        # Telemetry / State
        hide_telemetry = any(n in low for n in negations) and ("telemetría" in low or "telemetria" in low or "métrica" in low or "metrica" in low or "estado" in low or "health" in low)
        hide_telemetry = hide_telemetry or any(k in low for k in ["sin telemetría", "sin telemetria", "sin métricas", "sin metricas", "sin estado", "sin health"])
        
        # Report / Action / Mode
        hide_report = any(n in low for n in negations) and ("modo reporte" in low or "reporte" in low or "paso" in low or "acción" in low or "accion" in low or "dump" in low)
        hide_report = hide_report or any(k in low for k in ["sin modo reporte", "sin reporte", "sin plan", "sin paso", "sin acción", "sin accion", "sin modo"])
        
        # Audit / Scaling
        hide_audit = any(k in low for k in ["sin auditoría", "sin auditoria", "sin profunda", "no me vendas", "no me escales", "sin escalar", "no me cierres"])
        
        # Block / Roadmap
        hide_block = any(n in low for n in negations) and ("bloque" in low or "roadmap" in low)
        hide_block = hide_block or any(k in low for k in ["sin bloques", "sin bloque", "sin roadmap"])

        # Runtime logs/telemetry
        hide_runtime = any(k in low for k in ["sin runtime", "sin logs", "sin sistema", "limpio"]) or hide_telemetry

        # 4. Final Policy Assignment
        return cls(
            show_telemetry = not hide_telemetry,
            show_header = not (is_minimal or any(k in low for k in ["corto", "limpio", "sin modo", "sin encabezado"]) or hide_report),
            show_action = not hide_report,
            show_footer = not (is_minimal or hide_audit or hide_report),
            is_minimal = is_minimal,
            is_brief = is_brief,
            is_report_mode = not hide_report,
            suppress_audit = hide_audit or is_minimal,
            suppress_block = hide_block or is_minimal,
            suppress_runtime = hide_runtime or is_minimal,
            tone = "natural" if any(k in low for k in ["criollo", "hablame", "chat", "natural", "contame", "che"]) else "executive"
        )

# Global helper for quick policy check
def get_output_policy(query: str) -> OutputPolicy:
    return OutputPolicy.from_query(query)
