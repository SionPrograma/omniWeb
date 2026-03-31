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
    def from_query(cls, query: str, surface: str = "chat"):
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

        # 4. Surface Defaults (Surgical context injection)
        tone_default = "executive"
        report_default = not hide_report
        
        if surface == "chat":
            # In Chat, default to natural voice unless explicit technical keywords
            is_explicit_tech = any(k in low for k in ["reporte", "detalle", "análisis", "analisis", "pasos", "plan", "por qué", "por que", "paso a paso", "diagnosis"])
            tone_default = "natural" if not is_explicit_tech else "executive"
            report_default = is_explicit_tech
            
            # Additional Chat cleanup
            is_brief = is_brief or not is_explicit_tech
            hide_runtime = hide_runtime or not is_explicit_tech
            hide_block = hide_block or not is_explicit_tech

        # 5. Final Policy Assignment
        return cls(
            show_telemetry = not hide_telemetry,
            show_header = not (is_minimal or any(k in low for k in ["corto", "limpio", "sin modo", "sin encabezado"]) or not report_default),
            show_action = report_default,
            show_footer = not (is_minimal or hide_audit or not report_default),
            is_minimal = is_minimal,
            is_brief = is_brief,
            is_report_mode = report_default,
            suppress_audit = hide_audit or is_minimal or not report_default,
            suppress_block = hide_block or is_minimal or not report_default,
            suppress_runtime = hide_runtime or is_minimal,
            tone = "natural" if any(k in low for k in ["criollo", "hablame", "chat", "natural", "contame", "che"]) else tone_default
        )

# Global helper for quick policy check
def get_output_policy(query: str, surface: str = "chat") -> OutputPolicy:
    return OutputPolicy.from_query(query, surface=surface)
