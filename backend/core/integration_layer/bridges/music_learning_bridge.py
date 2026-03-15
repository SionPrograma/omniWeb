import logging
from typing import Dict, Any
from ..domain_bridge import DomainBridge
from ..event_bus import integration_bus
from backend.core.education_engine.learning_path_generator import learning_path_generator

logger = logging.getLogger(__name__)

class MusicLearningBridge(DomainBridge):
    """
    Connects Music Intelligence with Education and Learning Paths.
    Translates practice results into educational progress and milestones.
    """
    def __init__(self):
        super().__init__("music_learning_bridge", ["music", "education", "skill_engine"])

    async def initialize(self):
        integration_bus.subscribe_to_domain("music_pattern_mastered", self.on_pattern_mastered)
        integration_bus.subscribe_to_domain("music_analyzed", self.on_music_analysis)
        logger.info("MusicLearningBridge: Creative education links active.")

    async def shutdown(self):
        pass

    async def on_pattern_mastered(self, payload: Dict[str, Any]):
        user_id = payload.get("user_id", "default_user")
        pattern_name = payload.get("pattern_name")
        difficulty = payload.get("difficulty", 1.0)
        
        logger.info(f"MusicLearningBridge: Pattern '{pattern_name}' mastered. Generating skill signal.")
        
        # Emit skill detection signal
        await integration_bus.emit_domain_event(
            "skill_detected",
            {"user_id": user_id, "metric_name": "rhythmic_precision", "score": 0.05 * difficulty},
            "music_intelligence"
        )

    async def on_music_analysis(self, payload: Dict[str, Any]):
        """Triggered during real-time music analysis."""
        # Could update current learning path progress here
        pass

music_learning_bridge = MusicLearningBridge()
