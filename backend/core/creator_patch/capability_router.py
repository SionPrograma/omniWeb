"""
Capability Router — OMNI_PATCH Phase C.
Translates intent and command data into specific capability requirements.
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

class CapabilityRouter:
    """
    Decides the technical path for a Creator mission.
    """

    def route(self, command: Any) -> Dict[str, Any]:
        # Support both dictionary and CreatorCommand object
        if hasattr(command, 'intent'):
            intent = command.intent
            raw_input = command.raw_input
        else:
            intent = command.get("intent", "unknown")
            raw_input = command.get("raw_input", "")

        logger.info(f"[CAPABILITY_ROUTER] Routing intent: {intent}")

        # OMNI_PATCH (Phase D): Check for OSS alternatives
        from .oss_model_registry import oss_model_registry
        oss_alternatives = []
        if intent in {"audit", "review", "compare", "system_audit"}:
            oss_alternatives = oss_model_registry.find_by_type("reasoning")
        elif intent in {"patch", "healing", "edit"}:
            oss_alternatives = oss_model_registry.find_by_type("code")

        # Review/Audit Capabilities
        if intent in {"system_audit", "remediation", "audit", "review", "compare"}:
            return {
                "capability_class": "OPERATIONAL_AUDIT",
                "needs_approval": False,
                "strategy": "evidence_first",
                "tools": ["system_state", "master_logbook", "runtime_truth"],
                "oss_models": [m.capability_id for m in oss_alternatives]
            }

        # Code/Patching Capabilities
        if intent in {"patch_proposal", "healing", "patch", "edit", "refactor"}:
            return {
                "capability_class": "CODE_MUTATION",
                "needs_approval": True,
                "strategy": "sandbox_first",
                "tools": ["file_system", "diff_engine", "shadow_worker"],
                "oss_models": [m.capability_id for m in oss_alternatives]
            }

        # Knowledge/Documentation
        if intent in {"search_knowledge", "summarize_cluster", "documentation", "summarize"}:
            return {
                "capability_class": "KNOWLEDGE_SYNTHESIS",
                "needs_approval": False,
                "strategy": "semantic_search",
                "tools": ["semantic_memory", "knowledge_graph"]
            }

        # Mission Orchestration
        if intent in {"mission_intake", "swarm_orchestration", "creator_plan"}:
            return {
                "capability_class": "SWARM_ORCHESTRATION",
                "needs_approval": True,
                "strategy": "multi_step_planning",
                "tools": ["mission_planner", "task_decomposer"]
            }

        # Default / Natural Chat
        return {
            "capability_class": "GENERAL_CONVERSATION",
            "needs_approval": False,
            "strategy": "natural_language",
            "tools": ["chat_processor"]
        }

capability_router = CapabilityRouter()
