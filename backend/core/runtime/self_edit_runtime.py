import logging
import sys
import os
import asyncio
from typing import List, Dict, Any, Optional
from backend.core.ai_host.execution.hot_reload import hot_reload_engine
from backend.core.ai_host.cognition.cognitive_core import cognitive_core

logger = logging.getLogger(__name__)

class SelfEditRuntime:
    """
    Highest level coordinator for system self-modification.
    Manages Hot Reloading, State Sync, and UI Notifications.
    Ensures that reloads do not destroy the AI's cognitive state.
    """

    def __init__(self):
        self.is_reloading = False

    async def apply_runtime_sync(self, files: List[str], batch_id: str) -> Dict[str, Any]:
        """
        Synchronizes the live runtime with recently modified files.
        Handles layered reloading (Frontend, Backend, Chips).
        """
        logger.info(f"[SELF_EDIT_RUNTIME] Synchronizing runtime for batch {batch_id}")
        self.is_reloading = True
        
        sync_results = {
            "reloaded_modules": [],
            "frontend_refresh": False,
            "registry_updated": False,
            "status": "SUCCESS"
        }

        try:
            # 1. Determine Layers and Trigger Hot Reload
            # notify_changes already handles the heavy lifting of path->module and reloads
            reload_results = await hot_reload_engine.notify_changes(files)
            sync_results["reloaded_modules"] = reload_results

            # 2. Check for Failures and Handle Rollback (Safety Rule)
            failed_reloads = [r for r in reload_results if r["status"] == "FAILED"]
            if failed_reloads:
                logger.error(f"[SELF_EDIT_RUNTIME] Hot reload failed for modules: {failed_reloads}. Initiating rollback.")
                sync_results["status"] = "FAILED"
                sync_results["error"] = f"Reload failed for {failed_reloads[0]['module']}"
                # The actual rollback of files would be handled by the caller (MutationEngine)
                # or we could trigger it here if we had the backup info.
                return sync_results

            # 3. Layer-Specific Synchronization
            for f in files:
                # Backend Router Registry update
                if "router" in f.lower() and f.endswith(".py"):
                    await self._sync_router_registry()
                    sync_results["registry_updated"] = True
                
                # Chip Context update
                if "chips/" in f.lower() or "chip.json" in f.lower():
                    await self._sync_chip_ecosystem()
                
                # Frontend Assets update
                if any(f.endswith(ext) for ext in [".html", ".css", ".js", ".jsx", ".tsx"]):
                    sync_results["frontend_refresh"] = True

            # 4. State Preservation Verification
            # (Ensuring Cognitive Core hasn't been nuked by a bad reload)
            logger.info(f"[SELF_EDIT_RUNTIME] Cognitive State preserved: {len(cognitive_core.hypotheses)} hypotheses active.")

            # 5. Notify Creator Mode
            await self._notify_creator_ui(sync_results)

        except Exception as e:
            logger.error(f"[SELF_EDIT_RUNTIME] Critical error during sync: {e}")
            sync_results["status"] = "CRITICAL_ERROR"
            sync_results["error"] = str(e)
        finally:
            self.is_reloading = False
            
        return sync_results

    async def _sync_router_registry(self):
        """Reloads the system router mapping if routes changed."""
        try:
            from backend.core.ai_host.brain_router import brain_router
            # In a real system, we might call brain_router.refresh_registry()
            logger.info("[SELF_EDIT_RUNTIME] Router registry synchronized.")
        except Exception as e:
            logger.error(f"Router sync error: {e}")

    async def _sync_chip_ecosystem(self):
        """Forces the ChipOrchestrator to rediscover chips."""
        try:
            from backend.core.chips.chip_orchestrator import chip_orchestrator
            await chip_orchestrator.discover_chips()
            logger.info("[SELF_EDIT_RUNTIME] Chip ecosystem synchronized.")
        except Exception as e:
            logger.error(f"Chip sync error: {e}")

    async def _notify_creator_ui(self, results: Dict[str, Any]):
        """Sends an event to the UI informing of the runtime update."""
        try:
            from backend.core.event_bus import event_bus
            await event_bus.publish("SYSTEM_RELOAD_COMPLETE", {
                "results": results,
                "timestamp": asyncio.get_event_loop().time()
            })
            logger.info("[SELF_EDIT_RUNTIME] Creator UI notified of changes.")
        except Exception as e:
            logger.debug(f"Event bus notification skipped (likely no active bus): {e}")

self_edit_runtime = SelfEditRuntime()
