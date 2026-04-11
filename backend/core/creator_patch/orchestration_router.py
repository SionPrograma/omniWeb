"""
Orchestration Router — OMNI_PATCH Phase I.
The unified entry point for Creator-governed missions.
"""

import logging
from typing import Dict, Any, Optional
from .capability_router import capability_router
from .response_critic import response_critic
from .evaluation_ledger import evaluation_ledger, EvaluationEntry

logger = logging.getLogger(__name__)

class CreatorOrchestrationRouter:
    """
    Final Unison Layer. 
    Harmonizes Command -> Capability -> Execution -> Review -> Ledger.
    """

    def __init__(self):
        self.router = capability_router
        self.critic = response_critic
        self.ledger = evaluation_ledger

    def process_command(self, creator_command: Any, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculates the technical path for a normalized command.
        """
        logger.info(f"[ORCHESTRATION_ROUTER] Routing command: {creator_command.intent}")
        route = self.router.route(creator_command)
        
        # Enforce safety/oss suggestions
        if route.get("oss_alternative"):
            logger.info(f"[ORCHESTRATION_ROUTER] OSS Alternative suggested: {route['oss_alternative']}")
            
        return route

    def finalize_interaction(self, response_data: Dict[str, Any], mission_context: Dict[str, Any]):
        """
        Final safety review and ledger recording.
        """
        critique = self.critic.review(response_data, mission_context)
        
        # Record to ledger
        from .creator_command_gateway import CreatorCommand
        command = mission_context.get("command")
        intent = command.intent if isinstance(command, CreatorCommand) else "unknown"
        
        entry = EvaluationEntry(
            mission_id=mission_context.get("mission_id", "global"),
            provider="omni_native",
            model_name="omni_v1",
            capability_type=intent,
            success=response_data.get("status") == "success",
            tests_passed=critique.get("useful", False),
            creator_approved=False,
            notes=critique.get("notes", "")
        )
        self.ledger.record(entry)
        
        return critique

orchestration_router = CreatorOrchestrationRouter()
