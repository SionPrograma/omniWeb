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
            proposal["risk"] = f"CRÍTICO: {compatibility_warning} (Riesgo de regresión móvil)"

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
        
        # Systemic Impact
        impact = "CRÍTICO" if "CRÍTICO" in str(proposal.get("risk")) else "BAJO (Aislado)"
        if "regresión" in str(proposal.get("risk")).lower():
            impact = "MEDIO (Posible regresión en mobile)"

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
        """Scans code content for real architectural issues/smells."""
        issues = []
        path_lower = path.lower()
        
        # 1. Detect JS/TS specific smells
        if path_lower.endswith((".js", ".ts")):
            if ' onclick="' in content or ' onchange="' in content or ' oninput="' in content:
                issues.append({
                    "problem": "Event handlers inlined (onclick/oninput) detectados.",
                    "change": "Refactorizar a event listeners desacoplados (addEventListener) para mejorar CPS y mantenibilidad.",
                    "risk": "MEDIO (Mantenibilidad)"
                })
            elif "console.log" in content or "console.warn" in content:
                issues.append({
                    "problem": "Uso de console logs detectado.",
                    "change": "Migrar logs a la infraestructura de logbook/telemetry centralizada.",
                    "risk": "BAJO (Limpieza)"
                })
            elif "var " in content:
                issues.append({
                    "problem": "Uso de 'var' detectado (Legacy JS).",
                    "change": "Refactorizar a let/const para garantizar scope de bloque.",
                    "risk": "BAJO (Estabilidad)"
                })
        
        # 2. Detect Python smells
        elif path_lower.endswith(".py"):
            if "print(" in content:
                issues.append({
                    "problem": "Uso de print() para debugging detectado.",
                    "change": "Reemplazar prints con logging.info/error para telemetría persistente.",
                    "risk": "BAJO"
                })
            elif "except:" in content or "except Exception:" in content:
                issues.append({
                    "problem": "Cláusulas try/except genéricas.",
                    "change": "Especificar excepciones puntuales para evitar silenciar errores críticos.",
                    "risk": "MEDIO (Visibilidad de fallos)"
                })

        # 3. Global smells: Long Blocks
        lines = content.splitlines()
        if len(lines) > 150:
             issues.append({
                "problem": "Archivo con alta densidad de líneas (>150).",
                "change": "Descomponer el módulo en componentes más pequeños y especializados.",
                "risk": "MEDIO (Mantenibilidad)"
             })

        if not issues:
            return {
                "problem": "No se detectaron debilidades críticas inmediatas.",
                "change": "Auditoría nominal: Mantener estado actual y vigilar evolutivos.",
                "risk": "NULO"
            }
            
        # Return the most relevant (first) issue found
        return issues[0]
