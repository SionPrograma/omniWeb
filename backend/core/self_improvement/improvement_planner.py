import logging
from typing import List, Dict, Any
from .friction_detector import friction_detector

logger = logging.getLogger(__name__)

class ImprovementPlanner:
    """
    Transforms detected friction into actionable system improvement proposals.
    """
    def plan_optimizations(self) -> List[Dict[str, Any]]:
        """
        Creates a list of optimization proposals based on usage friction.
        """
        frictions = friction_detector.detect_repeated_manual_switching()
        frictions += friction_detector.detect_frequent_commands_without_workflow()
        
        proposals = []
        for f in frictions:
            if f["cause"] == "frequent_app_switching":
                proposals.append({
                    "proposal_type": "workflow_creation",
                    "description": f"Crear un flujo de trabajo para coordinar {f['involved_chips']}.",
                    "recommended_action": f"workflow_create_{'_'.join(f['involved_chips'])}",
                    "meta": f
                })
            elif f["cause"] == "lack_of_automation":
                proposals.append({
                    "proposal_type": "automation_suggestion",
                    "description": f"Automatización detectada: La intención '{f['intent']}' es común. ¿Crear un atajo?",
                    "recommended_action": f"automate_{f['intent']}",
                    "meta": f
                })
        return proposals

improvement_planner = ImprovementPlanner()
