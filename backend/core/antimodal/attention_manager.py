import time
import logging
from typing import Optional
from .antimodal_models import AntimodalMode, AntimodalState

logger = logging.getLogger(__name__)

class AttentionManager:
    """
    Determines how much interface intensity should be used.
    Integrates signals from user activity, context engine, and active workflows.
    """
    def __init__(self):
        self.state = AntimodalState(
            current_mode=AntimodalMode.STANDARD,
            last_interaction_timestamp=time.time()
        )

    def update_interaction(self):
        """Called when user interacts to refresh activity status."""
        self.state.last_interaction_timestamp = time.time()
        # Potential: reduce intensity/reset if user is active

    def decide_mode(self, current_context: dict) -> AntimodalMode:
        """
        Dynamically decide which mode to suggest or apply.
        """
        if not self.state.auto_adapt:
            return self.state.current_mode

        # Rules from specification:
        # - user is in focused work session
        # - repeated interruptions are not useful
        # - same workflow is already running
        # - user prefers compact interaction

        # Placeholder logic based on context data
        if current_context.get("is_focused", False):
            return AntimodalMode.LOW_DISTRACTION
        
        if current_context.get("repeated_task", False):
            return AntimodalMode.COMPACT

        return self.state.current_mode

    def set_mode(self, mode: AntimodalMode):
        logger.info(f"Antimodal mode change: {self.state.current_mode} -> {mode}")
        self.state.current_mode = mode

    def get_intensity(self) -> float:
        """Returns intensity level (0.0 to 1.0)."""
        mode_map = {
            AntimodalMode.STANDARD: 1.0,
            AntimodalMode.LOW_DISTRACTION: 0.4,
            AntimodalMode.COMPACT: 0.6,
            AntimodalMode.SILENT: 0.1,
            AntimodalMode.BACKGROUND: 0.2,
            AntimodalMode.SUMMARY_ONLY: 0.5
        }
        return mode_map.get(self.state.current_mode, 1.0)

attention_manager = AttentionManager()
