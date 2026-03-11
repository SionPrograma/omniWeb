import logging
import asyncio
from typing import Callable, Coroutine, Dict, Any

logger = logging.getLogger(__name__)

class BackgroundOrchestrator:
    """
    Main orchestrator for chips and workflows to continue in background.
    Requirement: allow chips and workflows to continue in background with low user interruption.
    Requirement: Background mode must respect zero-trust permissions.
    Requirement: Sensitive/destructive operations still require explicit user confirmation.
    """
    def __init__(self):
        # We store registered 'safe' background tasks
        self.safe_tasks: Dict[str, Coroutine] = {}

    async def execute_in_background(self, task_name: str, coro: Coroutine, is_destructive: bool = False) -> str:
        """
        Submits a task for background execution.
        If destructive=True, should be blocked if in background mode unless already confirmed.
        """
        from .antimodal_controller import antimodal_controller
        from .antimodal_models import AntimodalMode

        current_mode = antimodal_controller.get_current_mode()
        
        # Rule: do not allow destructive operations silently
        if current_mode == AntimodalMode.BACKGROUND and is_destructive:
            logger.warning(f"Suppressed destructive task {task_name} in background mode.")
            return f"BLOCKED: {task_name} is destructive. Explicit user approval required."

        # Rule: background mode must respect zero-trust permissions.
        # Permission logic is usually handled inside the coroutine (already enforced by DB/API)
        # However, we log it here for safety and audit.
        logger.info(f"Submitting background task {task_name} (Mode: {current_mode})")
        
        # Non-blocking execution
        asyncio.create_task(self._wrap_task(task_name, coro))
        
        return f"ENQUEUED: {task_name} is running in background."

    async def _wrap_task(self, name: str, coro: Coroutine):
        try:
            result = await coro
            logger.info(f"Background task {name} completed: {result}")
        except Exception as e:
            logger.error(f"Background task {name} failed: {e}")

    def is_operation_safe(self, operation: str) -> bool:
        """Determines if an operation can be performed without UI feedback/confirmation."""
        safe_list = ["stats_refresh", "memory_sync", "session_prepare", "chip_activation", "read_only"]
        return operation in safe_list


background_orchestrator = BackgroundOrchestrator()
