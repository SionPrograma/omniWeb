import os
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger(__name__)

class CopilotSafetyPolicy:
    """
    Harden the internal copilot against known failure patterns.
    Enforces surgical precision and runtime truth.
    """
    
    # --- FAILURE PATTERNS ---
    REJECTED_PATTERNS = [
        "claiming success without proof",
        "changing multiple systems without request",
        "introducing regressions",
        "silent replacement of working logic",
        "fake evidence",
        "breaking mobile/legacy compatibility"
    ]

    # --- FORBIDDEN FILES ---
    FORBIDDEN_FILES = [".env", "omniweb.db", "backend.db", "venv", ".venv", ".git"]

    @classmethod
    def validate_proposal(cls, proposal: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validates a proposal against the safety policy.
        """
        issues = []
        
        # 1. Scope Check
        target_files = proposal.get("files", [])
        if len(target_files) > 3:
            issues.append("Propuesta demasiado amplia (> 3 archivos). Se requiere aprobación especial.")
            
        # 2. Path Validation
        for file in target_files:
            if any(forbidden in file for forbidden in cls.FORBIDDEN_FILES):
                issues.append(f"Acceso denegado a archivo restringido: {file}")
                
        # 3. Compatibility Check (Heuristic)
        # Note: In a real system, this would perform deeper analysis
        if proposal.get("risk") == "Nulo" and proposal.get("diff"):
             # Safety warning: never claim nulo risk if changing code
             proposal["risk"] = "Bajo (Intervención de código detectada)"

        return {
            "is_safe": len(issues) == 0,
            "issues": issues,
            "policy_version": "1.0.0-hardened"
        }

    @classmethod
    def generate_safety_footer(cls) -> str:
        return """
---
🛡️ **POLÍTICA DE SEGURIDAD ACTIVA:**
- Solo cambios quirúrgicos permitidos.
- Prohibida la mutación sin aprobación previa.
- Prioridad absoluta: Verdad en Runtime.
"""

    @classmethod
    def check_mobile_compatibility(cls, diff: str, target_files: List[str] = None) -> Optional[str]:
        """
        Warns if a diff or target file might break mobile editor or shell compatibility.
        """
        legacy_keywords = ["editor.js", "main.js", "read_file", "write_file", "/fs/"]
        
        # Check diff content
        if any(kw in diff for kw in legacy_keywords):
            return "ADVERTENCIA: El diff contiene cambios en flujos críticos de compatibilidad móvil."
            
        # Check file paths
        if target_files:
            for file in target_files:
                if any(kw in os.path.basename(file) or "/fs/" in file for kw in legacy_keywords):
                    return f"ADVERTENCIA: El archivo objetivo '{os.path.basename(file)}' es crítico para el shell móvil."
                    
        return None

safety_policy = CopilotSafetyPolicy()
