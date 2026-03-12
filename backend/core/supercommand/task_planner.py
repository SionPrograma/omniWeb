import logging
from typing import List, Dict, Any, Optional
from .supercommand_models import SuperPrompt, ExecutionStep, TaskCategory

logger = logging.getLogger(__name__)

class TaskPlanner:
    """Connects execution steps to real system modules."""
    
    def resolve_step(self, step: ExecutionStep, category: TaskCategory) -> Dict[str, Any]:
        """Maps a generic execution step to specific system operations."""
        # This is a simplified resolver; would normally call into the actual system services.
        mapping = {
            "Audit Subsystem": {"module": "stability_loop", "method": "audit", "args": []},
            "Search Knowledge": {"module": "semantic_layer", "method": "search", "args": []},
            "Audit Architecture": {"module": "stability_loop", "method": "audit", "args": ["architecture"]},
            "Define Environment": {"module": "omni_runtime", "method": "get_status", "args": []},
            "Baseline Audit": {"module": "stability_loop", "method": "audit", "args": []}
        }
        
        # Default or fallback
        op = mapping.get(step.name, {"module": "ai_host", "method": "process", "args": [step.action]})
        
        return {
            "task_id": step.id,
            "operation": op,
            "description": step.name,
            "action": step.action
        }

    def create_execution_plan(self, prompt: SuperPrompt) -> List[Dict[str, Any]]:
        """Transforms a SuperPrompt into a concrete list of operations."""
        plan = []
        for step in prompt.steps:
            plan.append(self.resolve_step(step, prompt.category))
        return plan

task_planner = TaskPlanner()
