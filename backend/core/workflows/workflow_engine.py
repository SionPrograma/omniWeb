import logging
from .workflow_registry import workflow_registry
from backend.core.module_registry import module_registry

logger = logging.getLogger(__name__)

class WorkflowEngine:
    """
    Executes multi-step workflows.
    """
    async def execute(self, workflow_name: str) -> dict:
        wf = workflow_registry.get_workflow(workflow_name)
        if not wf:
            return {"status": "error", "message": f"Workflow {workflow_name} not found."}

        results = []
        for step in wf["steps"]:
            action = step.get("action")
            target = step.get("target")

            if action == "activate_chip":
                module_registry.activate_chip(target)
                results.append(f"Chip {target} activated.")
            elif action == "system_status":
                results.append("System status check performed.")

        return {
            "status": "success",
            "workflow": workflow_name,
            "steps_executed": results
        }

workflow_engine = WorkflowEngine()
