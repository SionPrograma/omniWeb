import logging
import asyncio
from typing import Callable, Coroutine, Any
from .loop_models import TaskState, LoopStep, TaskAnalytics
from .stability_checker import stability_checker
from .repair_engine import repair_engine

logger = logging.getLogger(__name__)

class ExecutionCycle:
    """
    Handles step-by-step execution of system tasks.
    Requirement: 1 AUDIT -> 2 ANALYZE -> 3 PLAN -> 4 APPLY -> 5 TEST -> 6 VERIFY -> 7 REPAIR -> ...
    """
    def __init__(self, state: TaskState):
        self.state = state

    async def run_step(self, step: LoopStep, action: Callable[[], Coroutine]):
        """Executes a single step and updates state."""
        self.state.current_step = step
        logger.info(f"Loop Cycle {self.state.cycle_count} | Step: {step}")
        
        try:
            result = await action()
            self.state.history.append({"step": step, "status": "success", "result": str(result)})
            return result
        except Exception as e:
            logger.error(f"Step {step} failed: {e}")
            self.state.errors.append(str(e))
            self.state.history.append({"step": step, "status": "fail", "error": str(e)})
            raise

    async def verify_stability(self) -> bool:
        """Requirement: Step 6 VERIFY_STABILITY."""
        check = await stability_checker.check_all()
        self.state.is_stable = check["is_stable"]
        return check["is_stable"]

    async def perform_repair(self) -> bool:
        """Requirement: Step 7 IF FAIL -> REPAIR."""
        self.state.repair_attempts += 1
        check = await stability_checker.check_all()
        return await repair_engine.attempt_repair(check["details"])
