
import re
from typing import Dict, Any, List, Optional

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
            "intent": "🎯 **MISIÓN / OBJETIVO**",
            "touch": "📂 **ZONAS AFECTADAS**",
            "dont_touch": "🔒 **ZONAS PROTEGIDAS**",
            "risk": "🛡️ **SEGURIDAD Y RIESGO**",
            "evidence": "🧪 **EVIDENCIA**",
            "plan": "🗺️ **MAPA DE EJECUCIÓN**",
            "next": "🚀 **PRÓXIMO PASO**",
            "gate": "🛑 **APROBACIÓN REQUERIDA**",
            "action": "⚡ **ACCIÓN RECOMENDADA**"
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
        """Disciplined Workspace Output for Megaprompts - Hardened for Mobile (CAPA 4)"""
        labels = self.MEGAPROMPT_LABELS.get(lang, self.MEGAPROMPT_LABELS["es"])
        
        # 1. Actionable Summary (For quick mobile glance)
        risk_icon = "🟢" if not mission.is_ambiguous else "🟡"
        narrative = f"{labels['intent']}\n**{mission.mission_name}**\n> {mission.primary_objective}\n\n"
        
        # 2. Zones (Compact)
        touch_zones = ", ".join([f"`{f}`" for f in mission.critical_files]) or "Sistema Omnicore"
        narrative += f"{labels['touch']}: {touch_zones}\n"
        
        if mission.forbidden_layers:
            forbidden = ", ".join([f"`{z}`" for z in mission.forbidden_layers])
            narrative += f"{labels['dont_touch']}: {forbidden}\n"
        
        narrative += "\n"

        # 3. Execution Tree (Visible Trace)
        if tree and "root" in tree:
            narrative += f"{labels['plan']}\n"
            # Get only active or relevant phases to save vertical space on mobile
            phases = tree["root"].get("children", [])
            for phase in phases:
                phase_status = phase.get('status', 'PENDING')
                if phase_status not in ["ACTIVE", "NEEDS_REVIEW", "FAILED"] and len(phases) > 3:
                     # Skip completed/pending if too many to keep mobile view clean
                     continue
                
                mark = "✅" if phase_status in ["COMPLETADO", "COMPLETED"] else "⚛️" if phase_status == "ACTIVE" else "⏳"
                narrative += f"{mark} **{phase['label']}**\n"
                for task in phase.get("children", []):
                    status = task.get('status', 'PENDING')
                    icon = "✅" if status == "COMPLETED" else "🔥" if status == "ACTIVE" else "🚫" if status == "FAILED" else "⚠️" if status == "NEEDS_REVIEW" else "⏳"
                    narrative += f"    {icon} {task['label']}\n"
            narrative += "\n"
        
        # 4. Critical Status / Gate
        failed_node = self._find_failed(tree["root"].get("children", [])) if tree and "root" in tree else None
        
        if failed_node:
             narrative += f"> [!CAUTION]\n> **BLOQUEO:** `{failed_node['label']}` falló.\n"
             narrative += f"> **Motivo:** {failed_node.get('evidence', 'Sin evidencia física.')}\n\n"
             
             recovery = failed_node.get("metadata", {}).get("recovery_proposal")
             if recovery:
                 narrative += f"🛠️ **RECUPERACIÓN PROPUESTA**\n"
                 narrative += f"**{recovery['tactic']}**: {recovery['action']}\n\n"
                 narrative += f"{labels['action']}\nEscribí **'ejecutar recuperación'** o **'reintentá'**.\n\n"
        else:
             active_label = self._find_active_label(tree, "Siguiente microtarea")
             narrative += f"{labels['next']}\n`{active_label}`\n\n"
             
             # Clear call to action for Mobile
             narrative += f"{labels['action']}\nEscribí **'seguí'**, **'ok'** o **'adelante'** para proceder.\n\n"
        
        risk_level = "MÍNIMO" if not mission.is_ambiguous else "MODERADO"
        narrative += f"--- \n{risk_icon} {labels['risk']}: {risk_level} | Disciplina Operativa v2.5"
        
        return narrative.strip()

    def _find_failed(self, nodes: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        for n in nodes:
            if n.get("status") in ["FAILED", "NEEDS_REVIEW"]: return n
            found = self._find_failed(n.get("children", []))
            if found: return found
        return None

    def _find_active_label(self, tree: Dict[str, Any], default: str) -> str:
        active_id = tree.get("active_node_id")
        if not active_id or "root" not in tree: return default
        
        def search(nodes):
            for n in nodes:
                if n.get("id") == active_id: return n.get("label")
                res = search(n.get("children", []))
                if res: return res
            return None
        return search(tree["root"].get("children", [])) or default


copilot_normalizer = CopilotNormalizer()
