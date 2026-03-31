
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

    # MEGAPROMPT: DISCIPLINED OUTPUT CONTRACT (CAPA 4)
    MEGAPROMPT_LABELS = {
        "es": {
            "intent": "### MISIÓN ENTENDIDA",
            "touch": "### LO QUE VOY A TOCAR",
            "dont_touch": "### LO QUE NO VOY A TOCAR",
            "risk": "### RIESGO Y SEGURIDAD",
            "evidence": "### EVIDENCIA PREVIA",
            "plan": "### ÁRBOL DE EJECUCIÓN",
            "next": "### PRÓXIMO PASO",
            "gate": "### REQUIERE APROBACIÓN"
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
                        # Use partition to handle multiple colons
                        _, _, val = line.partition(":")
                        data[label] = val.strip()
                        break

        # Check for Megaprompt context
        compiled_mission = understanding.get("compiled_mission")
        if compiled_mission and source_surface == "workspace":
            return self._normalize_megaprompt(compiled_mission, task_tree, lang)

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

        # ... (conversational part follows)
    
    def _normalize_megaprompt(self, mission: Any, tree: Dict[str, Any], lang: str) -> str:
        """Disciplined Workspace Output for Megaprompts (CAPA 4)"""
        labels = self.MEGAPROMPT_LABELS.get(lang, self.MEGAPROMPT_LABELS["es"])
        
        narrative = f"{labels['intent']}\n{mission.mission_name}\n> {mission.primary_objective}\n\n"
        
        touch_zones = ", ".join([f"`{f}`" for f in mission.critical_files]) or "Sistema Omnicore"
        narrative += f"{labels['touch']}\n{touch_zones}\n\n"
        
        forbidden = "\n".join([f"- {z}" for z in mission.forbidden_layers]) or "Ninguna zona explícita."
        narrative += f"{labels['dont_touch']}\n{forbidden}\n\n"
        
        risk = "MÍNIMO" if not mission.is_ambiguous else "MODERADO"
        narrative += f"{labels['risk']}\nNivel: {risk} | Criterio: Disciplina de Árbol Operativo\n\n"
        
        if mission.is_ambiguous:
             narrative += f"> [!WARNING]\n> {mission.ambiguity_notes[0] if mission.ambiguity_notes else 'Ambigüedad detectada.'}\n\n"

        if tree and "root" in tree:
            # We show a simplified tree for the report
            narrative += f"{labels['plan']}\n"
            for phase in tree["root"].get("children", []):
                narrative += f"- {phase['label']} ({phase['status']})\n"
                for task in phase.get("children", []):
                    narrative += f"    - [{ 'x' if task['status'] == 'COMPLETED' else ' ' }] {task['label']}\n"
            narrative += "\n"
        
        narrative += f"{labels['next']}\nEjecución del primer nodo del árbol: `Fase 1: Auditar`.\n\n"
        narrative += f"{labels['gate']}\nSe requiere aprobación para iniciar la misión disciplinada."
        
        return narrative.strip()


copilot_normalizer = CopilotNormalizer()
