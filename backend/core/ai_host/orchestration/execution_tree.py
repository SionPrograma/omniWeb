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
    NEEDS_REVIEW = "NEEDS_REVIEW"
    RECOVERING = "RECOVERING"

class ExecutionNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4())[:8])
    label: str
    type: str # phase, subphase, task, validation, checkpoint
    status: NodeStatus = NodeStatus.PENDING
    children: List['ExecutionNode'] = Field(default_factory=list)
    description: str = ""
    
    # --- SELF-VERIFICATION LAYER (CAPA 1) ---
    success_criteria: List[str] = Field(default_factory=list)
    evidence: Optional[str] = None
    verification_type: str = "nominal" # nominal, diff, file_check, content_presence, runtime_check
    risk_rating: str = "LOW"
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

    def advance_active_node(self) -> Optional[str]:
        """CAPA 3: Sequential flow. Moves to next pending task ONLY if current is DONE."""
        flat = self.get_flat_tasks()
        
        # 1. Check current node status
        current_node = next((n for n in flat if n.id == self.active_node_id), None)
        if current_node and current_node.status not in [NodeStatus.COMPLETED, NodeStatus.SKIPPED]:
            # Current node is still active or failed/needs review. DO NOT advance.
            return self.active_node_id

        # 2. Find next pending
        found_current = False
        for node in flat:
            if node.id == self.active_node_id:
                found_current = True
                continue
            if found_current and node.status == NodeStatus.PENDING:
                self.active_node_id = node.id
                node.status = NodeStatus.ACTIVE
                return node.id
        
        # No more tasks
        self.active_node_id = None
        return None

    def activate_recovery(self, node_id: str):
        """CAPA 5: Recovery Loop. Resets a FAILED node to RECOVERING."""
        def traverse(node):
            if node.id == node_id:
                node.status = NodeStatus.RECOVERING
                node.evidence = f"[RECOVERY] Iniciando táctica correctiva..."
                return True
            for child in node.children:
                if traverse(child): return True
            return False
        traverse(self.root)

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
        audit_phase.children.append(ExecutionNode(
            label="Scan de Superficie", 
            type="task", 
            description="Identificar archivos y capas afectadas.",
            verification_type="nominal",
            success_criteria=["Capas objetivo identificadas"]
        ))
        audit_phase.children.append(ExecutionNode(
            label="Pre-flight Check", 
            type="validation", 
            description="Verificar que no hay bloqueos previos.",
            verification_type="nominal",
            success_criteria=["Sistema en estado nominal"]
        ))
        
        # Fase 2: Implementación Aditiva
        impl_phase = ExecutionNode(label="Fase 2: Ejecución Quirúrgica", type="phase", description="Cambios mínimos y no destructivos.")
        
        if compiled_mission.plan_steps:
            # DYNAMIC STEPS (Phase 30 Saneamiento)
            for step in compiled_mission.plan_steps:
                impl_phase.children.append(ExecutionNode(
                    label=step,
                    type="task",
                    description="Paso definido en el Megaprompt.",
                    verification_type="nominal"
                ))
        else:
            # FALLBACK: Convert critical files into tasks
            for f in compiled_mission.critical_files[:3]: # Max 3 for first pass to keep it surgical
                f_name = f.split('/')[-1]
                task = ExecutionNode(
                    label=f"Modificar {f_name}", 
                    type="task", 
                    description=f"Implementación aditiva en {f}.",
                    verification_type="content_presence",
                    metadata={"target_file": f},
                    success_criteria=[f"Cambio persistido en {f_name}"]
                )
                impl_phase.children.append(task)
                
                val_task = ExecutionNode(
                    label=f"Validar {f_name}", 
                    type="validation", 
                    description="Confirmar estabilidad estructural.",
                    verification_type="file_check",
                    metadata={"target_file": f},
                    success_criteria=[f"Archivo {f_name} legible"]
                )
                impl_phase.children.append(val_task)
        
        # Checkpoint Final
        checkpoint = ExecutionNode(label="Fase 3: Cierre y Reporte", type="phase", description="Consolidar evidencia y reporte final.")
        checkpoint.children.append(ExecutionNode(
            label="Checkpoint de Evidencia", 
            type="checkpoint", 
            description="Registrar todos los cambios en MissionState.",
            verification_type="nominal",
            success_criteria=["MissionState persistido"]
        ))
        checkpoint.children.append(ExecutionNode(
            label="Reporte de Misión", 
            type="task", 
            description="Generar reporte final disciplinado.",
            verification_type="nominal",
            success_criteria=["Reporte enviado a Workspace"]
        ))

        root.children = [audit_phase, impl_phase, checkpoint]
        
        return ExecutionTree(
            mission_id=uuid.uuid4().hex[:12],
            root=root,
            active_node_id=audit_phase.children[0].id
        )


tree_planner = TreePlanner()
