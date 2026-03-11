import logging
from .loop_models import TaskAnalytics

logger = logging.getLogger(__name__)

class TaskAnalyzer:
    """
    Evaluates requested operations and determines execution steps.
    """
    def analyze(self, task_type: str, payload: dict) -> TaskAnalytics:
        logger.info(f"Analyzing task: {task_type}")
        
        # Risk levels
        risk_map = {
            "create_chip": 0.4,
            "modify_chip": 0.7,
            "install_plugin": 0.5,
            "apply_patch": 0.8,
            "system_upgrade": 0.9,
            "improvement_proposal": 0.6
        }
        
        risk = risk_map.get(task_type, 0.5)
        
        # Impacted services
        impacted = ["core"]
        if "chip" in task_type:
            target = payload.get("chip_slug") or payload.get("target")
            if target:
                impacted.append(target)
                
        return TaskAnalytics(
            estimated_risk=risk,
            impacted_services=impacted,
            requires_rollback_point=(risk > 0.3)
        )

task_analyzer = TaskAnalyzer()
