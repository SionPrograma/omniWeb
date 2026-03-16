from typing import Dict, Any, List, Optional
from enum import Enum

class PlanType(Enum):
    DIAGNOSTIC = "diagnostic"
    EXECUTION = "execution"
    CHIP_ACTION = "chip_action"
    SELF_EDIT = "self_edit"
    GENERAL = "general"

class TaskStep:
    def __init__(self, id: int, type: str, description: str):
        self.id = id
        self.type = type
        self.description = description

    def to_dict(self):
        return {"id": self.id, "type": self.type, "description": self.description}

class TaskPlan:
    """
    A structured plan object before execution.
    Contains goal, steps, and verification.
    """
    def __init__(self, goal: str, plan_type: PlanType):
        self.goal = goal
        self.type = plan_type
        self.steps: List[TaskStep] = []
        self.verification: List[str] = []

    def add_step(self, type: str, description: str):
        id = len(self.steps) + 1
        self.steps.append(TaskStep(id, type, description))

    def add_verification(self, description: str):
        self.verification.append(description)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "goal": self.goal,
            "type": self.type.value,
            "steps": [s.to_dict() for s in self.steps],
            "verification": self.verification
        }

class TaskPlanner:
    """
    The AI Host's Planning Layer.
    Converts complex prompts into structured task plan objects.
    """
    def create_plan(self, prompt: str, intent: str, lang: str = "es") -> TaskPlan:
        """Generates a structured plan based on the intent and prompt."""
        p = prompt.lower()
        
        # 1. Self-Edit / Healing Plan
        if intent == "healing" or any(w in p for w in ["editar", "parchear", "patch", "self-edit", "corregir código", "repara", "arregla", "fix"]):
            plan = TaskPlan("Recuperar estabilidad del sistema (Healing)" if (intent == "healing" or "repara" in p) else ("Aplicar mejoras mediante el Self-Edit Loop" if lang == "es" else "Apply improvements via Self-Edit Loop"), PlanType.SELF_EDIT)
            plan.add_step("audit", "Auditar el archivo afectado e identificar el bloque crítico." if lang == "es" else "Audit target file and identify critical block.")
            plan.add_step("isolate", "Validar permisos y asegurar que no haya conflictos de guardado." if lang == "es" else "Validate permissions and ensure no write conflicts.")
            plan.add_step("patch", "Aplicar el parche y generar una copia de seguridad." if lang == "es" else "Apply patch and generate backup.")
            plan.add_step("verify", "Ejecutar la verificación del sistema." if lang == "es" else "Execute system verification.")
            plan.add_verification("Estado del sistema: HEALTHY" if lang == "es" else "System state: HEALTHY")
            return plan

        # 2. Chip Action Plan
        if intent in ["open_chip", "inspect_chip"] or "chip" in p:
             plan = TaskPlan("Operar sobre un chip del ecosistema" if lang == "es" else "Operate ecosystem chip", PlanType.CHIP_ACTION)
             plan.add_step("locate", "Localizar la ruta del chip en el registro." if lang == "es" else "Locate chip path in registry.")
             plan.add_step("launch", "Cargar el entorno de runtime (iframe/backend)." if lang == "es" else "Launch runtime environment.")
             plan.add_step("focus", "Transferir el contexto visual al chip seleccionado." if lang == "es" else "Transfer visual context to selected chip.")
             plan.add_verification("Conexión del chip establecida." if lang == "es" else "Chip connection established.")
             return plan

        # 3. Diagnostic Plan / System Improvement (Extended for Coordination Stage 9)
        if intent == "creator_analysis" or any(w in p for w in ["cuello de botella", "rendimiento", "analiza"]):
             plan = TaskPlan("Diagnosticar y proponer mejoras de arquitectura" if lang == "es" else "Diagnose and propose architecture improvements", PlanType.DIAGNOSTIC)
             plan.add_step("scan", "Escanear el estado de salud de todos los módulos." if lang == "es" else "Scan health of all modules.")
             plan.add_step("analyze", "Cruzar métricas de latencia con la carga actual del Host." if lang == "es" else "Cross-reference latency metrics with Host load.")
             
             # Coordination Step if requested
             if any(w in p for w in ["logbook", "guarda", "registra", "save"]):
                 plan.add_step("log", "Registrar los hallazgos en el chip Logbook." if lang == "es" else "Record findings in Logbook chip.")
             
             plan.add_step("propose", "Sugerir un plan de acción para resolver el cuello de botella." if lang == "es" else "Suggest action plan for bottleneck.")
             plan.add_verification("Reporte de diagnóstico generado exitosamente." if lang == "es" else "Diagnostic report successfully generated.")
             return plan

        # Default Generic Plan
        plan = TaskPlan("Ejecutar acción solicitada" if lang == "es" else "Execute requested action", PlanType.GENERAL)
        plan.add_step("process", "Procesar la intención detectada." if lang == "es" else "Process detected intent.")
        plan.add_step("notify", "Informar al creador del resultado." if lang == "es" else "Notify creator of result.")
        plan.add_verification("Respuesta enviada." if lang == "es" else "Response sent.")
        return plan

task_planner = TaskPlanner()
