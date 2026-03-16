import logging
import datetime
from enum import Enum
from typing import Dict, Any, List, Optional
from ..module_registry import module_registry

logger = logging.getLogger(__name__)

class ChipStatus(Enum):
    ACTIVE = "ACTIVE"
    IDLE = "IDLE"
    ERROR = "ERROR"
    DISABLED = "DISABLED"

class ChipState:
    def __init__(self, chip_id: str, status: ChipStatus = ChipStatus.IDLE):
        self.chip_id = chip_id
        self.status = status
        self.last_activity = None
        self.health = "healthy"
        self.context = {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chip_id": self.chip_id,
            "status": self.status.value,
            "last_activity": self.last_activity,
            "health": self.health,
            "context": self.context
        }

class ChipOrchestrator:
    """
    Central orchestration layer for OmniWeb chips.
    Coordinates multiple modules, tracks health, and routes ecosystem commands.
    """
    def __init__(self):
        self.chip_states: Dict[str, ChipState] = {}
        self._initialize_from_registry()

    def _initialize_from_registry(self):
        """Syncs with ModuleRegistry to discover chips."""
        chips = module_registry.discover_all_chips()
        for chip in chips:
            slug = chip["slug"]
            status = ChipStatus.IDLE if chip.get("active", True) else ChipStatus.DISABLED
            self.chip_states[slug] = ChipState(slug, status)
        logger.info(f"[ORCHESTRATOR] Initialized with {len(self.chip_states)} chips.")

    def get_all_chips_status(self) -> List[Dict[str, Any]]:
        """Returns the current state of all registered chips."""
        # Re-sync to catch new chips
        self._refresh_discovery()
        return [state.to_dict() for state in self.chip_states.values()]

    def is_valid_chip(self, chip_id: str) -> bool:
        """Checks if a chip ID matches a registered chip or alias."""
        if not chip_id: return False
        if chip_id in self.chip_states: return True
        
        # Try a fresh discovery
        self._refresh_discovery()
        return chip_id in self.chip_states

    def _refresh_discovery(self):
        """Checks for new chips without resetting existing states."""
        all_chips = module_registry.discover_all_chips()
        for chip in all_chips:
            slug = chip["slug"]
            if slug not in self.chip_states:
                status = ChipStatus.IDLE if chip.get("active", True) else ChipStatus.DISABLED
                self.chip_states[slug] = ChipState(slug, status)

    async def activate_chip(self, chip_id: str) -> bool:
        """Activates a chip and sets its status to ACTIVE."""
        if chip_id not in self.chip_states:
            # Try to discover if it's new
            self._refresh_discovery()
            if chip_id not in self.chip_states:
                logger.info(f"[ORCHESTRATOR] Creating placeholder state for unknown chip: {chip_id}")
                self.chip_states[chip_id] = ChipState(chip_id, ChipStatus.IDLE)

        state = self.chip_states[chip_id]

        self.chip_states[chip_id].status = ChipStatus.ACTIVE
        self.chip_states[chip_id].last_activity = datetime.datetime.now().isoformat()
        logger.info(f"[ORCHESTRATOR] Chip '{chip_id}' activated.")
        
        # --- STAGE 11: Update Cognitive Core ---
        self._update_cognitive_core_state()
        
        return True

    async def deactivate_chip(self, chip_id: str) -> bool:
        """Deactivates a chip and sets its status to IDLE."""
        if chip_id in self.chip_states:
            self.chip_states[chip_id].status = ChipStatus.IDLE
            logger.info(f"[ORCHESTRATOR] Chip '{chip_id}' set to IDLE.")
            
            # --- STAGE 11: Update Cognitive Core ---
            self._update_cognitive_core_state()
            
            return True
        return False

    def _update_cognitive_core_state(self):
        """Pushes active chips list to cognitive core."""
        try:
            from ..ai_host.cognition.cognitive_core import cognitive_core
            active = [cid for cid, s in self.chip_states.items() if s.status == ChipStatus.ACTIVE]
            cognitive_core.update_world_state(active_chips=active)
        except Exception as e:
            logger.error(f"Orchestrator: Failed to update Cognitive Core: {e}")

    async def route_command(self, chip_id: str, action: str, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Routes a specific command to a chip."""
        if chip_id not in self.chip_states:
            return {"success": False, "error": f"Chip '{chip_id}' not found."}

        state = self.chip_states[chip_id]
        if state.status == ChipStatus.DISABLED:
            return {"success": False, "error": f"Chip '{chip_id}' is disabled."}

        # Update last activity
        state.last_activity = datetime.datetime.now().isoformat()
        
        # Placeholder for actual chip routing (Stage 10+ will use dynamic IPC)
        logger.info(f"[ORCHESTRATOR] Routing '{action}' to chip '{chip_id}' with params: {params}")
        
        # Simulation of chip communication
        return {
            "success": True,
            "chip_id": chip_id,
            "action": action,
            "timestamp": state.last_activity,
            "result": f"Action '{action}' executed successfully on chip '{chip_id}'."
        }

    def share_context(self, source_chip: str, target_chip: str, context_data: Dict[str, Any]):
        """Passes context between chips."""
        if source_chip in self.chip_states and target_chip in self.chip_states:
            self.chip_states[target_chip].context.update({
                "from": source_chip,
                "data": context_data,
                "timestamp": datetime.datetime.now().isoformat()
            })
            logger.info(f"[ORCHESTRATOR] Context shared from '{source_chip}' to '{target_chip}'.")
            return True
        return False

chip_orchestrator = ChipOrchestrator()
