import logging
import os
import difflib
import re
from typing import Dict, Any, Optional, List
from .base import CommandProcessor, AICommandResponse
from ..execution.safety_policy import safety_policy

logger = logging.getLogger(__name__)

class ProposalProcessor(CommandProcessor):
    """
    Anti-Gravity Interno: Proposal-only coding assistant (Harden Stage).
    Analyzes code and proposes minimal patches without auto-applying.
    Enforces strict safety workflow: AUDIT -> ISOLATE -> PROPOSE -> SHOW DIFF.
    """
    
    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        # 1. AUDIT & ISOLATE (Resolve Target)
        target_path = self._resolve_target(msg, context)
        if not target_path:
            # Requisito Omni: ARCHIVO_LEIDO: NONE if searching for open file fails
            return AICommandResponse(
                intent="proposal_error",
                status="success", # Using success status so it's not treated as a technical failure
                message="ARCHIVO_LEIDO: NONE"
            )

        # 2. FILE-SCOPE LOCK (Path Safety)
        if not self._is_safe_path(target_path):
            return AICommandResponse(
                intent="proposal_error",
                status="error",
                message=f"BLOQUEO DE SEGURIDAD: El archivo '{target_path}' está en la lista FORBIDDEN FILES."
            )

        # 3. READ (Audit Content)
        try:
            with open(target_path, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception as e:
            # Requisito Omni: ARCHIVO_LEIDO: NONE if file is not found or cannot be read
            return AICommandResponse(
                intent="proposal_error",
                status="success",
                message="ARCHIVO_LEIDO: NONE"
            )

        # 4. PROPOSE (Minimal Patch Only)
        proposal = self._generate_intelligent_proposal(target_path, original_content, msg)
        
        # 5. VALIDATE PROPOSAL (Internal Safety Layer)
        validation = safety_policy.validate_proposal({
            "files": [target_path],
            "diff": proposal.get("diff", ""),
            "risk": proposal.get("risk", "Bajo")
        })
        
        if not validation["is_safe"]:
            return AICommandResponse(
                intent="safety_violation",
                status="alert",
                message=f"VIOLACIÓN DE POLÍTICA: {', '.join(validation['issues'])}"
            )

        # 6. SHOW DIFF (Visual Evidence)
        diff_str = self._generate_diff(original_content, proposal["new_content"], target_path)
        
        # 7. COMPATIBILITY SCRUTINY (Mobile/Legacy check)
        compatibility_warning = safety_policy.check_mobile_compatibility(diff_str, target_files=[target_path])
        if compatibility_warning:
            previous_risk = proposal.get("risk", "")
            proposal["risk"] = f"CRÍTICO: {compatibility_warning} (Riesgo de regresión móvil). {previous_risk}"

        # 8. REPORT (Structured Form - Omni Directive)

        first_line = "None"
        if original_content:
            lines = original_content.splitlines()
            if lines:
                first_line = lines[0].strip()

        # Generate purposeful summary
        purpose = proposal.get("problem", "Propósito general del módulo.")
        if "audio" in target_path.lower() or "librosa" in target_path.lower() or "audio" in msg:
            purpose = "Gestión de procesamiento de audio y señales para transcripción liviana."
        
        # Microfix proposal
        microfix = proposal.get("change", "No se requiere cambio estructural inmediato.")
        
        # Systemic Impact (Surgical Specificity)
        raw_risk = str(proposal.get("risk", "BAJO (Aislado)"))
        impact = raw_risk # Default to the full specific risk string
        
        # Maintain severity prefix but keep the context
        if "regresión" in raw_risk.lower():
            if "MEDIO" not in raw_risk:
                impact = f"MEDIO (Posible regresión: {raw_risk})"
        elif "CRÍTICO" in raw_risk:
            impact = raw_risk


        formatted_message = f"""ARCHIVO_LEIDO: {target_path}
PRIMERA_LINEA: {first_line}
RESUMEN_REAL: {purpose}
MICROFIX_PROPUESTO: {microfix}
IMPACTO_RELACIONADO: {impact}

---
{diff_str or "# ARCHIVO BAJO AUDITORÍA (Sin cambios generados)"}"""

        return AICommandResponse(
            intent="copilot_proposal",
            status="success",
            message=formatted_message.strip(),
            payload={
                "target_files": [target_path],
                "allowed_files": [target_path],
                "forbidden_files": safety_policy.FORBIDDEN_FILES,
                "proposal": proposal,
                "diff": diff_str,
                "mode": "proposal_only",
                "safety_audit": validation
            }
        )

    def _resolve_target(self, msg: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        # Priority 1: Current Editor Path from context
        if context and "multimodal_evidence" in context:
            for item in context["multimodal_evidence"]:
                if item.get("type") == "current_file":
                    return item.get("path")
        
        # Priority 2: Mentioned in message
        match = re.search(r"en ([\w/\.-]+)", msg)
        if match:
            return match.group(1)
            
        return None

    def _is_safe_path(self, path: str) -> bool:
        abs_path = os.path.abspath(path)
        # Delegate to safety policy
        return not any(p in abs_path for p in safety_policy.FORBIDDEN_FILES)

    def _generate_intelligent_proposal(self, path: str, content: str, request: str) -> Dict[str, Any]:
        """
        Heuristic-based minimal proposal (Phase 10 Specificity).
        Inspects content for real patterns to generate situation-aware suggestions.
        """
        filename = os.path.basename(path).lower()
        new_content = content
        msg = request.lower()
        
        # 1. SCAN CONTENT FOR REAL ISSUES (Deeper Audit)
        found_issue = self._scan_content_for_real_issues(path, content)
        
        # 2. POPULATE DEFAULTS FROM SCAN
        problem = found_issue["problem"]
        hypothesis = "Propuesta basada en auditoría de patrones recurrentes."
        change = found_issue["change"]
        risk = found_issue["risk"]
        verification = "Inspección visual y validación en runtime."
        
        # 3. SPECIAL MISSION OVERRIDES (Librosa / Logging / etc.)
        if any(kw in msg for kw in ["audio", "transcription", "transcribir"]):
            problem = "Riesgo de uso de modelos pesados para transcripción."
            hypothesis = "Para este entorno, librosa ofrece un balance superior entre performance y precisión."
            change = "Implementar flujo de carga liviana con librosa.load()."
            new_content = content + "\n# Propuesta: Integración librosa (Surgical Assistant)\nimport librosa\n"
            risk = "Controlado (Aumento leve de dependencias)."
            
        elif ("log" in msg or "mejorá" in msg) and ".py" in filename:
            if "import logging" not in content:
                new_content = "import logging\n" + content
                problem = "Falta de instrumentación de auditoría."
                change = "Inyección de logging import."
                risk = "Mínimo."
            else:
                problem = "Logs insuficientes para trazabilidad."
                lines = content.splitlines()
                for i, line in enumerate(lines):
                    if "def " in line and ":" in line:
                        lines.insert(i+1, "    logging.info(\"[AUDIT] Operation started.\")")
                        break
                new_content = "\n".join(lines)
                change = "Minimal log injection in first function body."
                risk = "Bajo."
        
        return {
            "file": path,
            "problem": problem,
            "hypothesis": hypothesis,
            "change": change,
            "new_content": new_content,
            "risk": risk,
            "verification": verification
        }

    def _generate_diff(self, old: str, new: str, path: str) -> str:
        diff = difflib.unified_diff(
            old.splitlines(keepends=True),
            new.splitlines(keepends=True),
            fromfile=f"a/{path}",
            tofile=f"b/{path}",
            n=3
        )
        return "".join(list(diff))

    def _scan_content_for_real_issues(self, path: str, content: str) -> Dict[str, str]:
        """Scans code content for real architectural issues/smells with surgical specificity."""
        issues = []
        path_lower = path.lower()
        filename = os.path.basename(path)
        
        # 1. Detect JS/TS specific smells (Focus on Architecture & UX)
        if path_lower.endswith((".js", ".ts")):
            # A. Detect Long Render Methods (Specific to functions like renderLayout)
            # Strategy: Find innerHTML assignments with long templates or assignments
            inner_html_matches = list(re.finditer(r"(?:\.|)innerHTML\s*=\s*(`[\s\S]*?`|['\"][\s\S]*?['\"]|content)", content))
            for ih_match in inner_html_matches:
                ih_pos = ih_match.start()
                ih_val = ih_match.group(1)
                
                # Check if the assigned value is large
                val_lines = ih_val.count("\n")
                
                # Search backward for the method name
                prefix = content[max(0, ih_pos - 1500) : ih_pos]
                method_heads = list(re.finditer(r"(?:^|[ \t]+)(?:async\s+|)(\w+)\s*\([^)]*\)\s*\{", prefix, re.MULTILINE))
                
                if method_heads:
                    last_head = method_heads[-1]
                    method_name = last_head.group(1)
                    if method_name in ["if", "while", "for", "switch", "catch", "constructor"]:
                        continue
                    
                    is_render = method_name.lower().startswith("render")
                    # If it's a render method or the template is large (> 5 lines)
                    if is_render or val_lines > 5:
                        issues.append({
                            "problem": f"El método {method_name}() en {filename} mezcla lógica con templates HTML extensos.",
                            "change": f"extraer {method_name}() en helper separado para reducir mezcla entre render y estado",
                            "risk": "puede afectar inicialización visual del panel si se altera el orden de render"
                        })





            # B. Check for high density (over 500 lines) - prioritize this as well
            lines_count = len(content.splitlines())
            if lines_count > 500:
                 issues.append({
                    "problem": f"El módulo {filename} excede las 500 líneas (alta carga cognitiva).",
                    "change": "fragmentar el módulo en submódulos especializados por responsabilidad",
                    "risk": "incrementa la probabilidad de efectos secundarios al modificar funciones compartidas"
                 })

            if 'document.getElementById' in content:
                issues.append({
                    "problem": f"{filename} tiene un acoplamiento directo con IDs globales del DOM.",
                    "change": "centralizar selectores en un config de elementos o inyectar el root",
                    "risk": "puede romper la interactividad si cambia la estructura de index.html"
                })
            
            if 'var ' in content:
                issues.append({
                    "problem": f"Uso de 'var' detectado en {filename} (Legacy scope).",
                    "change": "migrar a const/let para prevenir fugas de scope",
                    "risk": "posibles colisiones de variables en closures asincrónicos"
                })
        
        # 2. Detect Python smells (Focus on Router/Logic separation)
        elif path_lower.endswith(".py"):

            if "router.py" in path_lower and ("db." in content or "calculate_" in content or "Process" in content):
                issues.append({
                    "problem": f"Violación de capas en {filename}: lógica de negocio detectada en el Router.",
                    "change": "extraer lógica pesada a un Service Layer o Processor dedicado",
                    "risk": "dificulta el testeo unitario y la reutilización de la lógica central"
                })
            elif "except:" in content or "except Exception:" in content:
                issues.append({
                    "problem": f"Manejo de errores genérico en {filename}.",
                    "change": "reemplazar try-except genéricos por capturas de excepciones granulares",
                    "risk": "puede ocultar fallos de infraestructura críticos en producción"
                })

        # 3. Global Smells: Extreme Density
        lines_count = len(content.splitlines())
        if lines_count > 500:
             issues.append({
                "problem": f"El módulo {filename} excede las 500 líneas (alta carga cognitiva).",
                "change": "fragmentar el módulo en submódulos especializados por responsabilidad",
                "risk": "incrementa la probabilidad de efectos secundarios al modificar funciones compartidas"
             })

        if not issues:
            return {
                "problem": f"Análisis de {filename} concluido sin bloqueos críticos.",
                "change": "estabilizar y documentar puntos de extensión actuales",
                "risk": "BAJO (Aislado)"
            }
            
        # Prioritize according to specificity
        return issues[0]

