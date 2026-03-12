import logging
import uuid
import asyncio
from typing import Callable, Coroutine, Any, Dict, Optional
from .loop_models import TaskState, LoopStep, TaskAnalytics
from .task_analyzer import task_analyzer
from .execution_cycle import ExecutionCycle

logger = logging.getLogger(__name__)

class LoopController:
    """
    Central orchestrator that manages full audit -> execute -> repair cycles.
    """
    def __init__(self):
        self.active_tasks: Dict[str, TaskState] = {}

    async def execute_task(self, task_type: str, payload: dict, core_action: Callable[[], Coroutine]) -> tuple[TaskState, Any]:
        """
        Main entry point for Stability Loop execution.
        """
        task_id = str(uuid.uuid4())
        state = TaskState(task_id=task_id)
        self.active_tasks[task_id] = state
        
        cycle = ExecutionCycle(state)
        last_result = None
        
        try:
            # 1. AUDIT_SYSTEM
            await cycle.run_step(LoopStep.AUDIT, lambda: asyncio.sleep(0.1)) # Simulated initial audit
            
            # 2. ANALYZE_TASK
            analytics = task_analyzer.analyze(task_type, payload)
            
            # 3. PLAN_EXECUTION
            await cycle.run_step(LoopStep.PLAN, lambda: asyncio.sleep(0.1))
            
            while state.cycle_count < state.max_cycles:
                state.cycle_count += 1
                
                # 4. APPLY_CHANGE
                last_result = await cycle.run_step(LoopStep.EXECUTE, core_action)
                
                # 5. RUN_TESTS & 6. VERIFY_STABILITY
                is_stable = await cycle.verify_stability()
                
                if is_stable:
                    state.current_step = LoopStep.COMPLETE
                    logger.info(f"Task {task_id} completed successfully and stabilized.")
                    
                    # Knowledge Sync on Success (Phase R/S Stability Loop Integration)
                    if task_type in ["create_chip", "modify_system", "manual_sync"]:
                         try:
                             from backend.core.semantic_layer.embedding_synchronizer import embedding_synchronizer
                             await embedding_synchronizer.sync_all()
                             logger.info("Stability Loop: Semantic layer updated after success.")
                         except Exception as e:
                             logger.error(f"Post-task Semantic Sync failed: {e}")

                    return state, last_result
                
                # 7. IF FAIL -> REPAIR
                logger.warning(f"Task {task_id} is unstable. Attempting repair (Cycle {state.cycle_count}).")
                repaired = await cycle.perform_repair()
                
                if not repaired:
                    logger.error(f"Repair failed in cycle {state.cycle_count}.")
            
            # If we reach here, max cycles exceeded
            state.current_step = LoopStep.ROLLBACK
            logger.error(f"Stability Loop failed to stabilize system for task {task_id} after {state.max_cycles} cycles.")
            
        except Exception as e:
            logger.error(f"Critical failure in Stability Loop: {e}")
            state.current_step = LoopStep.FAILED
            state.errors.append(str(e))
            
        return state, last_result

    def get_task_status(self, task_id: str) -> Optional[TaskState]:
        return self.active_tasks.get(task_id)

loop_controller = LoopController()
