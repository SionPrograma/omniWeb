import logging
from typing import List, Dict, Any
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .context_model import context_model

logger = logging.getLogger(__name__)

class PreferenceEngine:
    """
    Analyzes preferences such as most used chips and common intents.
    """
    def detect_preferences(self):
        """
        Analyzes statistics to build a preference model.
        """
        from backend.core.usage.usage_tracker import usage_tracker
        with set_chip_context("core"):
            try:
                stats = usage_tracker.get_statistics()
                # Use most used chips to build preference
                for chip in stats["top_chips"]:
                    if chip["count"] >= 5:
                        context_model.save_pattern(
                            "preference",
                            {"preference_type": "favorite_chip", "chip": chip["slug"]},
                            confidence=0.5
                        )
                
                # Check interaction style (text only if user never uses voice, etc.)
                # TBD when voice is fully integrated
                context_model.save_pattern(
                    "preference",
                    {"preference_type": "interaction_style", "style": "text_heavy"},
                    confidence=1.0
                )
            except Exception as e:
                logger.error(f"PreferenceEngine: Failed to detect preferences: {e}")

preference_engine = PreferenceEngine()
