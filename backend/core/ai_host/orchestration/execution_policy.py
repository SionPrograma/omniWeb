
from enum import Enum
from typing import Dict, Any, List

class ExecutionMaturity(Enum):
    READY = "READY_FOR_PARTIAL_REPLACEMENT"
    SUPERVISED = "USE_WITH_SUPERVISION"
    NOT_READY = "TODAVÍA_NO_APTO"
    RISKY = "RIESGOSO_PARA_ESTA_TAREA"
    ESCALATE = "ESCALAR_A_ANTIGRAVITY"

class RiskLevel(Enum):
    LOW = "BAJO"
    MEDIUM = "MEDIO"
    HIGH = "ALTO"
    CRITICAL = "CRÍTICO"

class TaskExecutionPolicy:
    """
    Daily Execution Policy Engine for OmniWeb AI Host.
    Determines if a task can be handled by Copilot, needs supervision, or must escalate.
    """
    
    # 7.1 Taxonomy of Tasks vs Maturity
    TASK_MAP = {
        "memory_query": ExecutionMaturity.READY,
        "audit_file": ExecutionMaturity.READY,
        "read_context": ExecutionMaturity.READY,
        "impact_analysis": ExecutionMaturity.SUPERVISED,
        "risk_classification": ExecutionMaturity.READY,
        "microfix_proposal": ExecutionMaturity.SUPERVISED,
        "complex_patch": ExecutionMaturity.ESCALATE,
        "architecture_decision": ExecutionMaturity.NOT_READY,
        "multi_file_refactor": ExecutionMaturity.ESCALATE
    }

    CORE_LAYERS = ["backend/core", "chips/chip-base", "backend/core/security", "backend/core/ai_host"]

    def evaluate(self, task_type: str, target_path: str = "", affected_count: int = 1) -> Dict[str, Any]:
        """
        Evaluates a task against the execution policy.
        """
        maturity = self.TASK_MAP.get(task_type, ExecutionMaturity.NOT_READY)
        risk = RiskLevel.LOW
        
        # Risk Heuristics
        is_core = any(core in target_path for core in self.CORE_LAYERS)
        if is_core:
            risk = RiskLevel.HIGH if maturity == ExecutionMaturity.READY else RiskLevel.CRITICAL
        
        if affected_count > 3:
            risk = RiskLevel.HIGH if risk != RiskLevel.CRITICAL else risk
            
        if "auth" in target_path or "permission" in target_path or "state" in target_path:
            risk = RiskLevel.CRITICAL
            
        # Decision Logic
        action = "Ejecutar directamente"
        if maturity == ExecutionMaturity.ESCALATE or risk == RiskLevel.CRITICAL:
            action = "ESCALAR A ANTIGRAVITY"
            maturity = ExecutionMaturity.ESCALATE
        elif maturity == ExecutionMaturity.SUPERVISED or risk == RiskLevel.HIGH:
            action = "Requerir revisión del Creador"
            maturity = ExecutionMaturity.SUPERVISED
        elif risk == RiskLevel.LOW and maturity == ExecutionMaturity.READY:
            action = "Autónomo (Auditado)"
            
        return {
            "task_type": task_type,
            "maturity": maturity.value,
            "risk": risk.value,
            "is_core": is_core,
            "action": action,
            "rationale": self._generate_rationale(maturity, risk, is_core)
        }

    def _generate_rationale(self, maturity: ExecutionMaturity, risk: RiskLevel, is_core: bool) -> str:
        if risk == RiskLevel.CRITICAL:
            return "Afecta componentes de seguridad, estado o auth críticos. Bloqueado para Copilot."
        if is_core:
            return "Toca capas del kernel del sistema. Requiere supervisión absoluta."
        if maturity == ExecutionMaturity.ESCALATE:
            return "La complejidad de la tarea excede el umbral de las heurísticas actuales."
        return "Tarea dentro del rango operativo de confianza del Copilot."

execution_policy = TaskExecutionPolicy()
