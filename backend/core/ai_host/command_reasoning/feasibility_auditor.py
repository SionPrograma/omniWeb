import logging
from typing import Tuple, List, Optional
from .mission_planner import MissionPlan, MissionStep

logger = logging.getLogger(__name__)

class FeasibilityAuditor:
    """
    Verifies mission plans for safety, architectural conflicts, and feasibility.
    Refines or splits tasks if risks are detected.
    """
    
    async def audit_plan(self, plan: MissionPlan) -> Tuple[bool, MissionPlan, List[str]]:
        logger.info(f"[FEASIBILITY_AUDITOR] Auditing plan: {plan.title}")
        
        risks = []
        is_safe = True
        
        # 1. CHECK SCALE VS COMPLEXITY
        if plan.scale == "architecture" and len(plan.steps) < 5:
            risks.append("Architecture-scale mission requires more granular decomposition.")
            is_safe = False
            
        # 2. CHECK FOR MISSING SIMULATION
        has_sim = any(s.type == "simulation" for s in plan.steps)
        if not has_sim:
            risks.append("Mission lacks a safety simulation step.")
            is_safe = False
            
        # 3. CONSTRAINTS VALIDATION
        if any("break" in c.lower() for c in plan.constraints):
            # Ensure isolation step exists
            has_isolation = any("isolation" in s.task.lower() for s in plan.steps)
            if not has_isolation:
                risks.append("Plan involves stability constraints but lacks explicit isolation analysis.")
                is_safe = False

        # REFINE PLAN IF UNSAFE
        refined_plan = plan
        if not is_safe:
            logger.warning(f"[FEASIBILITY_AUDITOR] Plan flagged as UNSAFE. Refining...")
            refined_plan = await self._refine_plan(plan, risks)
            
        return is_safe, refined_plan, risks

    async def _refine_plan(self, plan: MissionPlan, risks: List[str]) -> MissionPlan:
        """Adds missing safety steps or splits risky tasks."""
        new_steps = list(plan.steps)
        
        if "Mission lacks a safety simulation step." in risks:
            # Insert simulation before implementation tasks
            exec_idx = next((i for i, s in enumerate(new_steps) if s.type == "execution"), len(new_steps)-1)
            
            sim_step = MissionStep(
                id=99, # Temporary
                task="Mandatory Safety Simulation",
                description="Refined plan: Added safety simulation per auditor requirement.",
                dependencies=[new_steps[exec_idx-1].id] if exec_idx > 0 else [],
                type="simulation"
            )
            new_steps.insert(exec_idx, sim_step)
            
            # Map of old IDs to new IDs for dependency updates
            id_map = {}
            for i, step in enumerate(new_steps):
                old_id = step.id
                step.id = i + 1
                id_map[old_id] = step.id
            
            # Update dependencies
            for step in new_steps:
                if step.id == 99: continue # Already handled
                step.dependencies = [id_map.get(d, d) for d in step.dependencies]
        else:
            # Simple re-index
            for i, step in enumerate(new_steps):
                step.id = i + 1
            
        return MissionPlan(
            title=f"{plan.title} [REFINED]",
            creator_command=plan.creator_command,
            interpreted_goal=plan.interpreted_goal,
            steps=new_steps,
            scale=plan.scale,
            constraints=plan.constraints,
            risks=plan.risks,
            success_criteria=plan.success_criteria,
            affected_layers=plan.affected_layers
        )

feasibility_auditor = FeasibilityAuditor()
