import logging
import datetime
from typing import List, Dict, Any
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .context_model import context_model

logger = logging.getLogger(__name__)

class RoutineAnalyzer:
    """
    Analyzes time-based behavioral patterns.
    """
    def detect_routines(self):
        """
        Analyzes the time of day and user activity to detect routines.
        """
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # Get recent events with time
                    rows = conn.execute(
                        "SELECT event_type, chip_slug, timestamp FROM usage_events ORDER BY timestamp DESC LIMIT 200"
                    ).fetchall()
                    
                    # Detect morning / evening routines
                    mornings = {} # 06:00 - 12:00
                    evenings = {} # 18:00 - 00:00
                    
                    for r in rows:
                        dt = datetime.datetime.fromisoformat(r["timestamp"])
                        hour = dt.hour
                        
                        if 6 <= hour < 12:
                            mornings[r["chip_slug"]] = mornings.get(r["chip_slug"], 0) + 1
                        elif 18 <= hour < 24:
                            evenings[r["chip_slug"]] = evenings.get(r["chip_slug"], 0) + 1
                            
                    # Save detected routines if frequency > 2
                    for chip, count in mornings.items():
                        if chip and count >= 3:
                            context_model.save_pattern(
                                "routine", 
                                {"routine_type": "morning", "chip": chip}, 
                                confidence=0.2 * count
                            )
                            
                    for chip, count in evenings.items():
                        if chip and count >= 3:
                            context_model.save_pattern(
                                "routine", 
                                {"routine_type": "evening", "chip": chip}, 
                                confidence=0.2 * count
                            )
            except Exception as e:
                logger.error(f"RoutineAnalyzer: Failed to detect routines: {e}")

routine_analyzer = RoutineAnalyzer()
