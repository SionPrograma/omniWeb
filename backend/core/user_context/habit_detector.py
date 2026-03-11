import logging
from typing import List, Dict, Any
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .context_model import context_model

logger = logging.getLogger(__name__)

class HabitDetector:
    """
    Analyzes user behavior to detect recurring habits.
    """
    def detect_habits(self, limit: int = 100):
        """
        Analyzes recent usage events to discover recurring sequences.
        """
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # Get recent chip access
                    rows = conn.execute(
                        "SELECT chip_slug FROM usage_events WHERE event_type = 'chip_opened' ORDER BY timestamp DESC LIMIT ?",
                        (limit,)
                    ).fetchall()
                    
                    slugs = [r["chip_slug"] for r in rows if r["chip_slug"]]
                    
                    # Detect pair habits (two chips frequently used one after another)
                    pairs = {}
                    for i in range(len(slugs) - 1):
                        pair = f"{slugs[i]}-{slugs[i+1]}"
                        pairs[pair] = pairs.get(pair, 0) + 1
                    
                    for p, count in pairs.items():
                        if count >= 3: # Threshold
                            chips = p.split("-")
                            context_model.save_pattern(
                                "habit", 
                                {"action": "sequential_open", "chips": chips},
                                confidence=0.1 * count
                            )
            except Exception as e:
                logger.error(f"HabitDetector: Failed to detect habits: {e}")

habit_detector = HabitDetector()
