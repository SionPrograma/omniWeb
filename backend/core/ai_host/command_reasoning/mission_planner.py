import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from .command_interpreter import InterpretedCommand

logger = logging.getLogger(__name__)

class MissionStep(BaseModel):
    id: int
    task: str
    description: str
    dependencies: List[int] = []
    type: str = "execution" # analysis, simulation, execution, audit

class MissionPlan(BaseModel):
    title: str
    creator_command: str
    interpreted_goal: str
    steps: List[MissionStep]
    scale: str
    constraints: List[str]
    depth: int = 1
    risks: List[str] = []
    success_criteria: List[str] = []
    affected_layers: List[str] = []
    
    def to_execution_tree(self) -> Dict[str, Any]:
        """Converts planar steps into a hierarchical tree for Pizarron."""
        root = {
            "label": self.title,
            "type": "mission",
            "status": "ACTIVE",
            "description": self.interpreted_goal,
            "children": []
        }
        
        # Simple Phase Grouping
        phases = {
            "analysis": {"label": "Fase de Análisis", "type": "phase", "status": "PENDING", "children": []},
            "execution": {"label": "Desarrollo & Implementación", "type": "phase", "status": "PENDING", "children": []},
            "audit": {"label": "Auditoría & Cierre", "type": "phase", "status": "PENDING", "children": []}
        }
        
        for s in self.steps:
            node = {
                "id": s.id,
                "label": s.task,
                "type": s.type,
                "status": "PENDING",
                "description": s.description
            }
            if s.type == "analysis":
                phases["analysis"]["children"].append(node)
                phases["analysis"]["status"] = "ACTIVE" # If analysis is first
            elif s.type in ["execution", "simulation"]:
                phases["execution"]["children"].append(node)
            else:
                phases["audit"]["children"].append(node)
                
        root["children"] = [p for p in phases.values() if p["children"]]
        return {"root": root}

class MissionPlanner:
    """
    Hardened Mission Planner.
    Converts interpreted command intent into a structured execution plan.
    Breaks goals into sequential and parallel steps.
    """
    
    async def create_plan(self, intent: InterpretedCommand) -> MissionPlan:
        logger.info(f"[PLANNER] Generating hardened plan for: {intent.goal} (Depth: {intent.analysis_depth})")
        
        steps = []
        
        # 1. STRUCTURAL ANALYSIS (Scaled by Depth)
        for i in range(intent.analysis_depth):
            step_id = len(steps) + 1
            steps.append(MissionStep(
                id=step_id,
                task=f"Structural Analysis L{i+1}",
                description=f"Deep inspection of {', '.join(intent.target_modules)} - Complexity Tier {i+1}",
                dependencies=[step_id - 1] if step_id > 1 else [],
                type="analysis"
            ))
        
        # 2. ISOLATION / CONSTRAINTS CHECK (High Priority)
        if intent.constraints:
            step_id = len(steps) + 1
            steps.append(MissionStep(
                id=step_id,
                task="Constraint Isolation",
                description=f"Identify real dependencies for: {', '.join(intent.constraints)}",
                dependencies=[step_id - 1],
                type="analysis"
            ))
        
        # 3. PROPOSAL / DESIGN
        step_id = len(steps) + 1
        steps.append(MissionStep(
            id=step_id,
            task="Target Implementation Design",
            description=f"Draft changes for goal: {intent.goal}",
            dependencies=[step_id - 1],
            type="execution"
        ))
        
        # 4. SIMULATION (Mandatory for Creator Commands)
        step_id = len(steps) + 1
        steps.append(MissionStep(
            id=step_id,
            task="Pre-Execution Simulation",
            description=f"Predict runtime impact for {intent.mission_scale} scale",
            dependencies=[step_id - 1],
            type="simulation"
        ))
        
        # 5. EXECUTION
        step_id = len(steps) + 1
        steps.append(MissionStep(
            id=step_id,
            task="Final Implementation",
            description="Apply changes to the target system",
            dependencies=[step_id - 1],
            type="execution"
        ))
        
        # 6. AUDIT
        step_id = len(steps) + 1
        steps.append(MissionStep(
            id=step_id,
            task="Architectural Audit",
            description="Verify alignment with design principles and constraints",
            dependencies=[step_id - 1],
            type="audit"
        ))
        
        plan = MissionPlan(
            title=f"MISSION: {intent.goal}",
            creator_command=intent.original_prompt,
            interpreted_goal=intent.goal,
            steps=steps,
            scale=intent.mission_scale,
            constraints=intent.constraints,
            depth=intent.analysis_depth,
            risks=intent.risks,
            success_criteria=intent.success_criteria,
            affected_layers=intent.affected_layers
        )
        
        logger.info(f"[PLANNER] Hardened Plan generated with {len(steps)} steps.")
        return plan

mission_planner = MissionPlanner()
