from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import uuid
from enum import Enum

class NodeStatus(str, Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"

class ExecutionNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str
    type: str # phase, subphase, task, validation, checkpoint
    status: NodeStatus = NodeStatus.PENDING
    children: List['ExecutionNode'] = Field(default_factory=list)
    description: str = ""
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # Recursive update (for Pydantic 2)
    def update_node(self, node_id: str, status: NodeStatus):
        if self.id == node_id:
            self.status = status
            return True
        for child in self.children:
            if child.update_node(node_id, status):
                return True
        return False

class ExecutionTree(BaseModel):
    """
    MEGAPROMPT EXECUTION LAYER - CAPA 3: EXECUTION TREE
    Hierarchical representation of a mission divided into phases and microtasks.
    Disciplines execution from massive changes to surgical steps.
    """
    mission_id: str
    root: ExecutionNode
    active_node_id: Optional[str] = None
    
    def get_flat_tasks(self) -> List[ExecutionNode]:
        """Returns all leaf nodes (tasks/validations)."""
        tasks = []
        def traverse(node):
            if not node.children:
                tasks.append(node)
                return
            for child in node.children:
                traverse(child)
        traverse(self.root)
        return tasks

    def get_progress(self) -> float:
        flat = self.get_flat_tasks()
        if not flat: return 0.0
        completed = [t for t in flat if t.status == NodeStatus.COMPLETED]
        return len(completed) / len(flat)

class TreePlanner:
    """
    Generates an ExecutionTree from a CompiledMission.
    """
    def generate(self, compiled_mission: Any) -> ExecutionTree:
        # Create Root (Mission)
        root = ExecutionNode(
            label=compiled_mission.mission_name,
            type="mission",
            description=compiled_mission.primary_objective
        )
        
        # Fase 1: Auditar (Surgical Pre-flight)
        audit_phase = ExecutionNode(label="Fase 1: Auditar", type="phase", description="Inspeccionar estado actual y dependencias.")
        audit_phase.children.append(ExecutionNode(label="Scan de Superficie", type="task", description="Identificar archivos y capas afectadas."))
        audit_phase.children.append(ExecutionNode(label="Pre-flight Check", type="validation", description="Verificar que no hay bloqueos previos."))
        
        # Fase 2: Implementación Aditiva
        impl_phase = ExecutionNode(label="Fase 2: Ejecución Quirúrgica", type="phase", description="Cambios mínimos y no destructivos.")
        
        # Convert critical files into tasks
        for f in compiled_mission.critical_files[:3]: # Max 3 for first pass to keep it surgical
            task = ExecutionNode(label=f"Modificar {f.split('/')[-1]}", type="task", description=f"Implementación aditiva en {f}.")
            impl_phase.children.append(task)
            impl_phase.children.append(ExecutionNode(label=f"Validar {f.split('/')[-1]}", type="validation", description="Confirmar estabilidad estructural."))
        
        # Checkpoint Final
        checkpoint = ExecutionNode(label="Fase 3: Cierre y Reporte", type="phase", description="Consolidar evidencia y reporte final.")
        checkpoint.children.append(ExecutionNode(label="Checkpoint de Evidencia", type="checkpoint", description="Registrar todos los cambios en MissionState."))
        checkpoint.children.append(ExecutionNode(label="Reporte de Misión", type="task", description="Generar reporte final disciplinado."))

        root.children = [audit_phase, impl_phase, checkpoint]
        
        return ExecutionTree(
            mission_id=uuid.uuid4().hex[:12],
            root=root,
            active_node_id=audit_phase.children[0].id
        )

tree_planner = TreePlanner()
