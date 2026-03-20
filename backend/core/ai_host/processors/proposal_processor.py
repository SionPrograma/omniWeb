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
            return AICommandResponse(
                intent="proposal_error",
                status="error",
                message="AUDIT FALLIDO: No se pudo aislar el archivo objetivo. Identificación requerida."
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
            return AICommandResponse(
                intent="proposal_error",
                status="error",
                message=f"ERROR DE AUDITORÍA: Lectura fallida {str(e)}"
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

        # 8. REPORT (Structured Form)
        formatted_message = f"""
### 🛡️ Propuesta de Edición Quirúrgica (Anti-Gravity Interno)

**ARCHIVO(S):** `{proposal['file']}`
**PROBLEMA AISLADO:** {proposal['problem']}
**CAUSA PROBABLE:** {proposal['hypothesis']}
**CAMBIO MÍNIMO PROPUESTO:** {proposal['change']}

**DIFF PREVIEW:**
```diff
{diff_str or "# No se detectaron cambios necesarios."}
```

**RIESGO:** {proposal['risk']}
**VERIFICACIÓN:** {proposal['verification']}
**ARCHIVOS NO TOCADOS:** Todos excepto `{proposal['file']}`
**ESPERANDO APROBACIÓN:** SÍ

---
⚠️ **ESTADO:** Analizado but NOT applied. Sin aprobación del Creator, no hay cambios en disco.
{safety_policy.generate_safety_footer()}
"""

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
        Heuristic-based minimal proposal.
        """
        filename = os.path.basename(path)
        new_content = content
        msg = request.lower()
        
        # Defaults
        problem = "Análisis solicitado."
        hypothesis = "Revisión general requerida."
        change = "Inyección de comentarios de auditoría para mejorar legibilidad."
        risk = "Mínimo (Solo comentarios)."
        verification = "Inspección visual."
        
        # Audio/Librosa Optimización
        if any(kw in msg for kw in ["audio", "transcription", "transcribir"]):
            problem = "Riesgo de uso de modelos pesados para transcripción."
            hypothesis = "Para este entorno, librosa ofrece un balance superior entre performance y precisión."
            change = "Implementar flujo de carga liviana con librosa.load()."
            new_content = content + "\n# Propuesta: Integración librosa (Surgical Assistant)\nimport librosa\n"
            risk = "Controlado (Aumento leve de dependencias)."
            verification = "Run audio-pipeline check."
            
        # Logging Inactivity
        elif "log" in msg or "mejorá" in msg:
            if ".py" in filename:
                if "import logging" not in content:
                    new_content = "import logging\n" + content
                    problem = "Falta de instrumentación de auditoría."
                    hypothesis = "Logs básicos son necesarios para el Runtime TRUTH Policy."
                    change = "Inyección de logging import."
                    risk = "Mínimo."
                    verification = "Reproduction of log lines in shell console."
                else:
                    problem = "Logs insuficientes para trazabilidad."
                    hypothesis = "Adding entry point logging improves audit fidelity."
                    lines = content.splitlines()
                    for i, line in enumerate(lines):
                        if "def " in line and ":" in line:
                            lines.insert(i+1, "    logging.info(\"[AUDIT] Operation started.\")")
                            break
                    new_content = "\n".join(lines)
                    change = "Minimal log injection in first function body."
                    risk = "Bajo."
                    verification = "Check backend logs after call."
        
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
