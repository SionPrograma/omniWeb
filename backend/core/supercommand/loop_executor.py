import logging
import asyncio
from typing import List, Dict, Any, Optional
from backend.core.stability_loop.loop_controller import loop_controller
from .supercommand_models import SuperPrompt, ExecutionStatus, SuperCommandResult

logger = logging.getLogger(__name__)

class LoopExecutor:
    """Executes a full SuperPrompt through the Stability Loop mechanism."""
    
    async def execute(self, prompt: SuperPrompt) -> SuperCommandResult:
        """Runs the multi-step SuperPrompt logic and updates its status as it goes."""
        logger.info(f"SuperCommand: Starting execution of task {prompt.task_id} - {prompt.title}")
        prompt.overall_status = ExecutionStatus.EXECUTING
        
        issues = []
        actions = []
        
        for step in prompt.steps:
            step.status = ExecutionStatus.EXECUTING
            logger.info(f"Executing step {step.id}: {step.name}")
            
            # Simulated Execution Wrapper
            async def run_step_op():
                # In a real implementation, this would call the results from task_planner
                # For now, we simulate a small delay and a system check.
                await asyncio.sleep(0.5)
                return {"success": True, "action": step.action}
            
            # Wrap the step with the Stability Loop!
            loop_state, result = await loop_controller.execute_task(
                f"supercommand_{step.name.lower().replace(' ', '_')}",
                run_step_op,
                {"step_id": step.id, "action": step.action}
            )
            
            from backend.core.stability_loop.loop_models import LoopStep
            if loop_state.current_step == LoopStep.FAILED:
                step.status = ExecutionStatus.FAILED
                error_msg = loop_state.errors[0] if loop_state.errors else "Unknown loop error"
                issues.append(f"Step {step.id} ({step.name}) failed: {error_msg}")
                prompt.overall_status = ExecutionStatus.FAILED
                break
            
            step.status = ExecutionStatus.VERIFIED
            actions.append(f"Performed: {step.action}")
            prompt.current_step_id = step.id
            
        success = prompt.overall_status != ExecutionStatus.FAILED
        if success:
            prompt.overall_status = ExecutionStatus.VERIFIED
            
        return SuperCommandResult(
            task_id=prompt.task_id,
            success=success,
            summary=f"Task {prompt.title} {'completed successfully' if success else 'failed'}.",
            issues_detected=issues,
            actions_performed=actions,
            stability_verified=success
        )

loop_executor = LoopExecutor()
