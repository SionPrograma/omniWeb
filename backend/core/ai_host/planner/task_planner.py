from typing import Dict, Any, List, Optional, Union
from enum import Enum
from pydantic import BaseModel, Field

# ---------------------------------------------------------
# 1. MODELOS DE DATOS ESTRUCTURADOS
# ---------------------------------------------------------

class PlanType(str, Enum):
    DIAGNOSTIC = "diagnostic"
    EXECUTION = "execution"
    CHIP_ACTION = "chip_action"
    SELF_EDIT = "self_edit"
    GENERAL = "general"


class ActionType(str, Enum):
    # Safe Actions
    SCAN = "scan"
    AUDIT = "audit"
    INSPECT = "inspect"
    ANALYZE = "analyze"
    SEARCH = "search"
    READ = "read"
    VERIFY = "verify"
    
    # Interaction Actions
    NOTIFY = "notify"
    LOG = "log"
    CLARIFY = "clarify"
    
    # Impact Actions (Unsafe)
    RESTART = "restart"
    CLEAN = "clean"
    MODIFY = "modify"
    PATCH = "patch"
    MUTATE = "mutate"
    SHUTDOWN = "shutdown"

class ActionableTask(BaseModel):
    id: int
    action_type: ActionType
    target_id: str = "system"
    parameters: Dict[str, Any] = Field(default_factory=dict)
    is_dangerous: bool = False
    requires_approval: bool = True
    reason: str = ""

    # Compatibilidad con ExecutionController antiguo
    @property
    def type(self) -> str:
        return self.action_type.value
    
    @property
    def description(self) -> str:
        return f"{self.action_type.upper()} on {self.target_id}: {self.reason}"

# Alias for compatibility with ExecutionController
TaskStep = ActionableTask


class TaskPlan(BaseModel):
    """
    Plan operativo estructurado. 
    Abandona la narrativa por una lista de ActionableTasks.
    """
    goal: str
    tasks: List[ActionableTask] = Field(default_factory=list)
    execution_mode: str = "sequential"
    confidence_score: float = 1.0
    clarification_needed: bool = False
    constraints: List[str] = Field(default_factory=list)
    missing_context: List[str] = Field(default_factory=list)

    # Compatibilidad con capas de síntesis y ejecución heredadas
    @property
    def steps(self) -> List[ActionableTask]:
        return self.tasks
    
    @property
    def verification(self) -> List[str]:
        return [f"Verify {t.action_type} outcome" for t in self.tasks if not t.is_dangerous]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "tasks": [t.dict() for t in self.tasks],
            "steps": [t.dict() for t in self.tasks], # Legacy support
            "execution_mode": self.execution_mode,
            "confidence_score": self.confidence_score,
            "clarification_needed": self.clarification_needed,
            "constraints": self.constraints
        }

# ---------------------------------------------------------
# 2. GENERADOR DE PLANES (PLANNER)
# ---------------------------------------------------------

class TaskPlanner:
    """
    Generador de misiones determinísticas de OpenWeb.
    Traduce diagnósticos técnicos en secuencias de tareas accionables.
    """

    def create_plan_from_diagnosis(self, diagnosis: Any, lang: str = "es") -> TaskPlan:
        """
        Toma un StructuredDiagnosis de runtime_truth y genera el plan operativo.
        """
        # Importación tardía para evitar círculo
        from ..reasoning.runtime_truth import DiagnosisCategory
        
        plan = TaskPlan(
            goal=f"Misión de {diagnosis.diagnosis_type}",
            confidence_score=diagnosis.confidence_score,
            clarification_needed=diagnosis.clarification_needed,
            constraints=diagnosis.constraints
        )

        dtype = diagnosis.diagnosis_type

        # 1. Mapeo Determinístico de Tareas por Tipo de Diagnóstico
        if dtype == DiagnosisCategory.LATENCY_SPIKE.value:
            plan.tasks.append(ActionableTask(
                id=1, action_type=ActionType.SCAN, target_id="system_bus", 
                reason="Escanear latencia de cada módulo conectado."
            ))
            plan.tasks.append(ActionableTask(
                id=2, action_type=ActionType.RESTART, target_id="gateway_bus", 
                is_dangerous=True, reason="Reiniciar bus de comunicación para purgar congestión."
            ))

        elif dtype == DiagnosisCategory.MEMORY_SATURATION.value:
            plan.tasks.append(ActionableTask(
                id=1, action_type=ActionType.INSPECT, target_id="os_memory", 
                reason="Identificar el proceso con mayor consumo de RAM."
            ))
            plan.tasks.append(ActionableTask(
                id=2, action_type=ActionType.CLEAN, target_id="omni_cache", 
                reason="Limpiar buffers temporales del sistema."
            ))

        elif dtype == DiagnosisCategory.CHIP_ERROR.value:
            # Intentar extraer el chip fallido de la evidencia
            culprit = "unknown_chip"
            if diagnosis.supporting_evidence:
                culprit = diagnosis.supporting_evidence[0].source
            
            plan.tasks.append(ActionableTask(
                id=1, action_type=ActionType.AUDIT, target_id=culprit, 
                reason=f"Verificar el estado de arranque del chip {culprit}."
            ))
            plan.tasks.append(ActionableTask(
                id=2, action_type=ActionType.RESTART, target_id=culprit, 
                is_dangerous=True, reason=f"Intentar reinicio frío del chip {culprit}."
            ))

        elif dtype == DiagnosisCategory.INSUFFICIENT_DATA.value or diagnosis.clarification_needed:
            plan.tasks.append(ActionableTask(
                id=1, action_type=ActionType.CLARIFY, target_id="user", 
                reason="Solicitar detalles específicos del síntoma reportado."
            ))

        else:
            # Caso Nominal o Desconocido
            plan.tasks.append(ActionableTask(
                id=1, action_type=ActionType.NOTIFY, target_id="user", 
                reason="Informar que el sistema está operando bajo parámetros normales."
            ))

        return plan

    # Compatibilidad para transición entre fases
    def create_plan(self, prompt: str, intent: str, lang: str = "es") -> TaskPlan:
        """
        Legacy entry point para cuando todavía no llega un diagnóstico estructurado.
        Simula un diagnóstico nominal para no romper el pipeline.
        """
        # Simulamos un objeto compatible con lo que espera el nuevo método
        class MockDiagnosis:
            diagnosis_type = "nominal"
            confidence_score = 0.9
            clarification_needed = False
            constraints = []
            supporting_evidence = []
            
        return self.create_plan_from_diagnosis(MockDiagnosis(), lang)

task_planner = TaskPlanner()
