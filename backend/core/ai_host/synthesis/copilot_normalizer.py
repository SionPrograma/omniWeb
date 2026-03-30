
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
        "en": {
            "finding": "**Finding:**",
            "safety": "**Security & Risk:**",
            "impact": "Impact:",
            "rec": "**Recommendation:**",
            "context": "I've analyzed the context of",
            "basis": "Analysis basis:",
            "no_change": "No structural mutations required."
        }
    }

    def normalize(self, text: str, understanding: Dict[str, Any], lang: str = "es", policy_result: Dict[str, Any] = None, task_tree: Dict[str, Any] = None) -> str:
        # Detect labels for all possible Copilot outputs
        lines = text.splitlines()
        data = {}
        target_labels = [
            "ARCHIVO_LEIDO", "RESUMEN_REAL", "IMPACTO_RELACIONADO", "CRITERIO_DE_SEGURIDAD", 
            "MICROFIX_PROPUESTO", "SCOPE_RAÍZ", "ARCHIVOS_RELEVANTES", "CAMBIO_PROPUESTO_POR_ARCHIVO"
        ]
        
        for line in lines:
            # Consistent Pass 5.2 Label Matching
            if ":" in line:
                for label in target_labels:
                    if line.strip().upper().startswith(label):
                        key, val = line.split(":", 1)
                        data[label] = val.strip()
                        break

        # print(f"[DEBUG] CopilotNormalizer data: {data.keys()}")
        # 1. Resolve Policy & Blocks Status
        show_heavy_blocks = policy_result.get("is_report_mode", True) if policy_result else True

        if not data and not policy_result:
            return text 
        
        if not data:
            # If no labels but policy exists, it's a technical fallback or audit without findings
            file_path = "Módulo del sistema"
            summary = text if len(text) < 200 else "Diagnóstico nominal completado."
            impact = "NULO"
            safety = "SEGURO"
            proposal = "Continuar con la operación estándar."
        else:
            # 1. Resolve Core Metadata
            file_path = data.get("ARCHIVO_LEIDO") or data.get("SCOPE_RAÍZ") or "Módulo del sistema"
            summary = data.get("RESUMEN_REAL") or data.get("CAMBIO_PROPUESTO_POR_ARCHIVO") or self.SEC_LABELS[lang]["no_change"]
            impact = data.get("IMPACTO_RELACIONADO", "Local")
            safety = data.get("CRITERIO_DE_SEGURIDAD", "SEGURO")
            proposal = data.get("MICROFIX_PROPUESTO") or (self.SEC_LABELS[lang]["no_change"] if "ninguno" in summary.lower() else "Seguir con el flujo actual.")
        
        # 2. Determine Title based on content and intent
        intent_group = understanding.get("intent_group", "")
        if "PROPOSAL" in intent_group or "propuesta" in text.lower() or "MICROFIX" in text.upper():
            title = self.TITLES[lang]["proposal"]
        elif "AUDIT" in intent_group or "audit" in text.lower() or "SCOPE_RAÍZ" in data:
            title = self.TITLES[lang]["audit"]
        else:
            title = self.TITLES[lang]["default"]

        # 3. Construct Unified Grammar Narrative
        labels = self.SEC_LABELS[lang]
        
        # Silent Director: No inyectamos títulos NUNCA en el chat principal. 
        # El título queda implícito o reservado para payloads técnicos.
        narrative = "" # Títulos Markdown eliminados del canal de voz principal.
        narrative += f"{labels['context']} `{file_path}`.\n\n"
        narrative += f"{labels['finding']} {summary}\n\n"
        narrative += f"{labels['safety']} {safety} | {labels['impact']} {impact}\n"
        
        if show_heavy_blocks and ("CORE" in str(impact).upper() or "ALTO" in str(safety).upper()):
            caution = "Dado que afecta a módulos centrales o críticos, se recomienda extrema precaución." if lang == "es" else "As this affects core or critical modules, extreme caution is recommended."
            narrative += f"> [!IMPORTANT]\n> {caution}\n"
            
        narrative += f"\n{labels['rec']} {proposal}\n"

        # 4. Footer & Diff preservation
        footer = "\n---\n"
        footer += f"ARCHIVO_AUDITADO: {file_path}\n"
        
        # Extract ORCHESTRATION_REPORT if present (from Tool Selection stage)
        orch_report = ""
        if "ORCHESTRATION_REPORT" in text.upper():
            try:
                # Find the block between labels if any, or just keep it as is
                orch_match = re.search(r'(### OMNI_WORK_ORCHESTRATION[\s\S]*?)---', text)
                if orch_match:
                    orch_report = orch_match.group(1).strip() + "\n"
            except: pass

        # 5. Policy Injection (Block 7)
        policy_block = ""
        if policy_result:
            p_lang = {
                "es": {"class": "**Clasificación:**", "risk": "**Riesgo:**", "action": "**Acción Operativa:**", "kernel": " kernel crítico"},
                "en": {"class": "**Classification:**", "risk": "**Risk:**", "action": "**Operational Action:**", "kernel": " critical kernel"}
            }[lang]
            
            p_title = "### POLÍTICA OPERATIVA DEL HOST" if lang == "es" else "### HOST OPERATIONAL POLICY"
            maturity = policy_result["maturity"]
            risk = policy_result["risk"]
            action = policy_result["action"]
            
            policy_block = f"\n\n{p_title}\n"
            policy_block += f"- {p_lang['class']} {maturity}\n"
            policy_block += f"- {p_lang['risk']} {risk}\n"
            policy_block += f"- {p_lang['action']} {action}\n"
            
            if policy_result.get("is_core"):
                policy_block += f"> [!CAUTION]\n> {policy_result['rationale']}\n" if lang == "es" else f"> [!CAUTION]\n> {policy_result['rationale']}\n"
        
        # 6. Task Tree Injection (Block 8)
        tree_block = ""
        if task_tree:
            t_lang = {
                "es": {"title": "### ÁRBOL SEMÁNTICO DE TRABAJO", "mission": "**Misión:**", "layer": "**Capa Objetivo:**", "tasks": "**Micro-tareas sugeridas (Surgical):**", "forbidden": "**Zonas Blindadas:**"},
                "en": {"title": "### SEMANTIC TASK TREE", "mission": "**Mission:**", "layer": "**Target Layer:**", "tasks": "**Suggested Micro-tasks (Surgical):**", "forbidden": "**Forbidden Zones:**"}
            }[lang]
            
            tree_block = f"\n\n{t_lang['title']}\n"
            tree_block += f"- {t_lang['mission']} {task_tree['summary']}\n"
            tree_block += f"- {t_lang['layer']} `{task_tree['primary_layer']}`\n"
            
            if task_tree['microtasks']:
                tree_block += f"\n{t_lang['tasks']}\n"
                for i, mt in enumerate(task_tree['microtasks'], 1):
                    tree_block += f"{i}. {mt}\n"
            
            if task_tree['forbidden_zones']:
                tree_block += f"\n{t_lang['forbidden']} " + ", ".join([f"`{z}`" for z in task_tree['forbidden_zones']]) + "\n"

        # Keep original diff
        diff_part = ""
        if "---" in text:
            parts = text.split("---")
            last_part = parts[-1]
            if "+" in last_part or "-" in last_part or "archivo_leido" in last_part.lower():
                diff_part = "\n---\n" + last_part.strip()

        if not show_heavy_blocks:
            return narrative.strip()

        # Silent Director: No inyectamos bloques de política o árbol en el string de retorno. 
        # Estos datos ya están en el payload para el Audit Drawer.
        return f"{narrative}{footer}{orch_report}{diff_part}".strip()

copilot_normalizer = CopilotNormalizer()
