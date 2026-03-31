
import re
from typing import Dict, Any, List

class CopilotNormalizer:
    """
    Transforms rigid technical Copilot data into human-legible, precise reports.
    Preserves OmniWeb format while adding executive clarity.
    Consistent Pass 5.2: Unified grammar and standardized sections.
    """
    
    # 5.2 Unified Grammatical Components
    TITLES = {
        "es": {
            "proposal": "### PROPUESTA DE MEJORA ESTRUCTURAL",
            "audit": "### INFORME DE AUDITORÍA TÉCNICA",
            "default": "### DIAGNÓSTICO Y ANÁLISIS"
        },
        "en": {
            "proposal": "### STRUCTURAL IMPROVEMENT PROPOSAL",
            "audit": "### TECHNICAL AUDIT REPORT",
            "default": "### DIAGNOSTIC & ANALYSIS"
        }
    }

    SEC_LABELS = {
        "es": {
            "finding": "**Hallazgo:**",
            "safety": "**Seguridad y Riesgo:**",
            "impact": "Impacto:",
            "rec": "**Recomendación:**",
            "context": "He analizado el contexto de",
            "basis": "Base del análisis:",
            "no_change": "No se requieren mutaciones estructurales."
        },
        # ... (en omitted for brevity in replace call, will preserve it)
    }

    # NEW: DISCIPLINED WORKSPACE TEMPLATE (BLOQUE 2)
    WORK_LABELS = {
        "es": {
            "explain": "### Explain",
            "audit": "### Audit",
            "fix": "### Suggest Fix",
            "refactor": "### Refactor",
            "preview": "### Patch Preview",
            "risk": "### Risk Assessment",
            "steps": "### Validation Steps"
        }
    }

    def normalize(self, text: str, understanding: Dict[str, Any], lang: str = "es", policy_result: Dict[str, Any] = None, task_tree: Dict[str, Any] = None, source_surface: str = "chat") -> str:
        # Detect labels for all possible Copilot outputs
        lines = text.splitlines()
        data = {}
        target_labels = [
            "ARCHIVO_LEIDO", "RESUMEN_REAL", "IMPACTO_RELACIONADO", "CRITERIO_DE_SEGURIDAD", 
            "MICROFIX_PROPUESTO", "SCOPE_RAÍZ", "ARCHIVOS_RELEVANTES", "CAMBIO_PROPUESTO_POR_ARCHIVO",
            "REFACTOR_ACORTADO", "PASOS_VALIDACIÓN"
        ]
        
        for line in lines:
            if ":" in line:
                for label in target_labels:
                    if line.strip().upper().startswith(label):
                        key, val = line.split(":", 1)
                        data[label] = val.strip()
                        break

        if not data and not policy_result:
            return text 
        
        # 1. Resolve Core Metadata
        file_path = data.get("ARCHIVO_LEIDO") or data.get("SCOPE_RAÍZ") or "Módulo del sistema"
        summary = data.get("RESUMEN_REAL") or data.get("CAMBIO_PROPUESTO_POR_ARCHIVO") or (self.SEC_LABELS[lang]["no_change"] if lang in self.SEC_LABELS else "No changes.")
        impact = data.get("IMPACTO_RELACIONADO", "Local")
        safety = data.get("CRITERIO_DE_SEGURIDAD", "SEGURO")
        proposal = data.get("MICROFIX_PROPUESTO") or "Seguir con el flujo actual."
        refactor = data.get("REFACTOR_ACORTADO", "Sin sugerencia.")
        steps = data.get("PASOS_VALIDACIÓN", "Validación nominal.")

        # --- BRANCH A: WORKSPACE MODE (DISCIPLINED & RIGID) ---
        if source_surface == "workspace":
            labels = self.WORK_LABELS.get(lang, self.WORK_LABELS["es"])
            w_narrative = f"{labels['explain']}\n{summary}\n\n"
            w_narrative += f"{labels['audit']}\nArchivo: `{file_path}`\nEstado: {safety}\n\n"
            w_narrative += f"{labels['fix']}\n{proposal}\n\n"
            w_narrative += f"{labels['refactor']}\n{refactor}\n\n"
            
            # Patch Preview is special, we only show header if there was a diff
            if "---" in text:
                w_narrative += f"{labels['preview']}\n(Ver panel de cambios para el diff detallado)\n\n"
            
            w_narrative += f"{labels['risk']}\nNivel: {impact} | Criterio: {safety}\n\n"
            w_narrative += f"{labels['steps']}\n{steps}"
            
            # Extra policy note if core
            if policy_result and policy_result.get("is_core"):
                w_narrative += f"\n\n> [!CAUTION]\n> {policy_result.get('rationale', 'Kernel system access.')}"
                
            return w_narrative.strip()

        # --- BRANCH B: CHAT MODE (CONVERSATIONAL & HUMAN) ---
        labels = self.SEC_LABELS[lang]
        
        # Narrative construction without hard headers
        narrative = f"{labels['context']} `{file_path}`. "
        
        # We transform the report into a sentence
        if "saludable" in summary.lower() or "ninguno" in summary.lower() or "no se requiere" in summary.lower():
            narrative += "Todo parece estar en orden y no he detectado anomalías estructurales."
        else:
            narrative += f"He identificado un posible ajuste: {summary}. "
            narrative += f"Mi recomendación técnica es: {proposal}."

        if "alto" in str(safety).lower() or "crítico" in str(safety).lower():
            narrative += f"\n\n⚠️ **Nota de seguridad:** Este cambio tiene un impacto {impact} y requiere precaución."

        return narrative.strip()

copilot_normalizer = CopilotNormalizer()
