from typing import Dict, Any
from .swarm_models import SwarmTask, TaskResult

class SwarmProtocol:
    """Defines the messaging format for the distributed swarm."""
    
    @staticmethod
    def wrap_task(task: SwarmTask) -> Dict[str, Any]:
        return {
            "bus_type": "swarm_task",
            "content": task.model_dump()
        }

    @staticmethod
    def wrap_result(result: TaskResult) -> Dict[str, Any]:
        return {
            "bus_type": "swarm_result",
            "content": result.model_dump()
        }
