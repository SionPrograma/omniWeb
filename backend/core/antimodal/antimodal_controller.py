import logging
from typing import Dict, Any, Optional
from .antimodal_models import AntimodalMode, AntimodalState, CompactResponse
from .attention_manager import attention_manager
from .compact_response import response_generator
from .silent_mode import silent_handler
from .background_orchestrator import background_orchestrator

logger = logging.getLogger(__name__)

class AntimodalController:
    """
    Main orchestrator for low-distraction operation modes.
    Manages state and bridges individual modes.
    Requirement: main orchestrator for low-distraction operation modes.
    """
    def __init__(self):
        self.state = attention_manager.state

    def set_mode(self, mode: AntimodalMode):
        """Enable or disable modes."""
        attention_manager.set_mode(mode)
        logger.info(f"System mode explicitly set to: {mode}")

    def get_current_mode(self) -> AntimodalMode:
        return self.state.current_mode

    def process_ai_response(self, response: str) -> str:
        """
        Adapts AI output based on active mode.
        Requirement: integrate Antimodal behavior with AI Host output.
        """
        mode = self.get_current_mode()
        
        # Responses in compact or summary_only modes
        if mode in [AntimodalMode.COMPACT, AntimodalMode.SUMMARY_ONLY]:
            compact = response_generator.summarize(response, mode)
            logger.info(f"AI response adapted (from {compact.original_length} chars to {len(compact.compact_text)})")
            return compact.compact_text
            
        return response

    def filter_ui_feedback(self, elements: list) -> list:
        """
        Filters UI components in silent/background modes.
        Requirement: silent mode suppression of rich UI.
        """
        if self.get_current_mode() in [AntimodalMode.SILENT, AntimodalMode.BACKGROUND]:
            return silent_handler.filter_ui_elements(elements)
        return elements

    def get_status_summary(self) -> Dict[str, Any]:
        """Provides status summary for dashboard and AI Host."""
        return {
            "mode": self.state.current_mode.value,
            "intensity": attention_manager.get_intensity(),
            "auto_adapt": self.state.auto_adapt,
            "is_silent": self.state.current_mode in [AntimodalMode.SILENT, AntimodalMode.BACKGROUND]
        }

antimodal_controller = AntimodalController()
