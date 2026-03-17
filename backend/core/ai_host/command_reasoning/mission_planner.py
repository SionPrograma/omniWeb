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

class MissionPlanner:
    """
    Converts interpreted command intent into a structured execution plan.
    Breaks goals into sequential and parallel steps.
    """
    
    async def create_plan(self, intent: InterpretedCommand) -> MissionPlan:
        logger.info(f"[PLANNER] Generating plan for: {intent.goal}")
        
        steps = []
        
        # 1. INITIAL ANALYSIS
        steps.append(MissionStep(
            id=1,
            task="Structural Analysis",
            description=f"Analyze current state of {', '.join(intent.target_modules)}",
            type="analysis"
        ))
        
        # 2. ISOLATION / CONSTRAINTS CHECK
        if intent.constraints:
            steps.append(MissionStep(
                id=2,
                task="Constraint Isolation",
                description=f"Identify dependencies for: {', '.join(intent.constraints)}",
                dependencies=[1],
                type="analysis"
            ))
        
        # 3. PROPOSAL / DESIGN
        last_id = len(steps)
        steps.append(MissionStep(
            id=last_id + 1,
            task="Target Implementation Design",
            description=f"Draft changes for goal: {intent.goal}",
            dependencies=[last_id],
            type="execution"
        ))
        
        # 4. SIMURATION (Mandatory for Creator Commands)
        last_id = len(steps)
        steps.append(MissionStep(
            id=last_id + 1,
            task="Pre-Execution Simulation",
            description="Predict runtime impact and stability",
            dependencies=[last_id],
            type="simulation"
        ))
        
        # 5. EXECUTION
        last_id = len(steps)
        steps.append(MissionStep(
            id=last_id + 1,
            task="Final Implementation",
            description="Apply changes to the target system",
            dependencies=[last_id],
            type="execution"
        ))
        
        # 6. AUDIT
        last_id = len(steps)
        steps.append(MissionStep(
            id=last_id + 1,
            task="Architectural Audit",
            description="Verify alignment with design principles and constraints",
            dependencies=[last_id],
            type="audit"
        ))
        
        plan = MissionPlan(
            title=f"MISSION: {intent.goal}",
            creator_command=intent.original_prompt,
            interpreted_goal=intent.goal,
            steps=steps,
            scale=intent.mission_scale,
            constraints=intent.constraints
        )
        
        logger.info(f"[PLANNER] Plan generated with {len(steps)} steps.")
        return plan

mission_planner = MissionPlanner()
