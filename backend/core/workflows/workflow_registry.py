from typing import Dict, List, Any

class WorkflowRegistry:
    """
    Registry for system workflows.
    """
    def __init__(self):
        self.workflows = {
            "prepare_work_session": {
                "name": "Preparar Sesión de Trabajo",
                "steps": [
                    {"action": "activate_chip", "target": "reparto"},
                    {"action": "activate_chip", "target": "finanzas"},
                    {"action": "system_status"}
                ]
            }
        }

    def get_workflow(self, name: str) -> Optional[Dict[str, Any]]:
        return self.workflows.get(name)

workflow_registry = WorkflowRegistry()
