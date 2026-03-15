import logging
import time
from typing import Dict, Any, Optional
from backend.core.module_registry import module_registry

logger = logging.getLogger(__name__)

class ActionExecutor:
    """
    Executes platform actions triggered by AI Host intents.
    Bridge between high-level commands and the UI/Runtime system.
    """
    
    def __init__(self):
        self.action_history = []

    async def execute(self, intent: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main entry point for action execution.
        """
        logger.info(f"[ACTION_INIT] Intent: {intent}")
        
        execution_result = {
            "success": False,
            "intent": intent,
            "actions_executed": [],
            "timestamp": time.time()
        }

        try:
            if intent == "open_chip":
                execution_result = await self._execute_open_chip(payload)
            elif intent == "inspect_chip":
                execution_result = await self._execute_inspect_chip(payload)
            elif intent == "navigate_to":
                execution_result = await self._execute_navigate_to(payload)
            elif intent == "focus_chip_runtime":
                execution_result = await self._execute_focus_chip(payload)
            else:
                logger.warning(f"[ACTION_SKIP] No specific executor for intent: {intent}")
                execution_result["message"] = f"No execution logic for {intent}"
                
            if execution_result.get("success"):
                logger.info(f"[ACTION_EXECUTED] Intent '{intent}' completed successfully.")
                self.action_history.append(execution_result)
            
        except Exception as e:
            logger.error(f"[ACTION_ERROR] Failed to execute {intent}: {e}")
            execution_result["error"] = str(e)
            execution_result["success"] = False

        return execution_result

    async def _execute_open_chip(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        if not target:
            return {"success": False, "error": "No target chip specified"}

        logger.info(f"[EXECUTION_STEP] Locating chip runtime: {target}")
        # Mark as active in registry for backend tracking
        module_registry.log_execution(target)
        
        # Simulate activation logic
        logger.info(f"[EXECUTION_STEP] Activating environment: {target}")
        
        return {
            "success": True,
            "intent": "open_chip",
            "actions_executed": [
                f"LOCATE_RUNTIME:{target}",
                f"ACTIVATE_ENVIRONMENT:{target}",
                "UPDATE_UI_LAUNCHER",
                "FOCUS_CHIP_PANEL"
            ],
            "target": target,
            "ui_instruction": {
                "action": "LAUNCH_CHIP",
                "target": target,
                "focus": True
            }
        }

    async def _execute_inspect_chip(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        return {
            "success": True,
            "intent": "inspect_chip",
            "actions_executed": [f"AUDIT_INTEGRITY:{target}", "FETCH_DATA_FLOW_METRICS"],
            "target": target,
            "ui_instruction": {
                "action": "INSPECT_CHIP",
                "target": target
            }
        }

    async def _execute_navigate_to(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("view") or payload.get("target")
        return {
            "success": True,
            "intent": "navigate_to",
            "actions_executed": [f"SWITCH_VIEW:{target}"],
            "target": target,
            "ui_instruction": {
                "action": "NAVIGATE",
                "view": target
            }
        }

    async def _execute_focus_chip(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        target = payload.get("target")
        return {
            "success": True,
            "intent": "focus_chip_runtime",
            "actions_executed": ["BRING_TO_FRONT", f"RESTORE_CONTEXT:{target}"],
            "target": target,
            "ui_instruction": {
                "action": "FOCUS",
                "target": target
            }
        }

action_executor = ActionExecutor()
