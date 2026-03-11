import logging
from typing import List, Dict, Any
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class PatternAnalyzer:
    """
    Analyzes system usage events to detect repetitive user behaviors.
    """
    def get_frequent_sequences(self, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Detects sequences of chips opened in short succession.
        """
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # Get the most recent events
                    rows = conn.execute(
                        "SELECT event_type, chip_slug, timestamp FROM usage_events ORDER BY timestamp DESC LIMIT ?",
                        (limit,)
                    ).fetchall()
                    
                    # Very simple pattern detection: consecutive events of certain types
                    patterns = []
                    for i in range(len(rows) - 1):
                        current = rows[i]
                        next_ev = rows[i+1]
                        
                        if current["event_type"] == next_ev["event_type"] == "ai_orchestration_command":
                            # Potential repeated orchestration
                            patterns.append({
                                "type": "repeated_orchestration",
                                "chips": [current["chip_slug"], next_ev["chip_slug"]]
                            })
                    return patterns
            except Exception as e:
                logger.error(f"PatternAnalyzer: Failed to fetch events: {e}")
                return []

    def get_most_common_intents(self) -> List[Dict[str, Any]]:
        """
        Analyzes AI Host telemetry to find most frequent intents.
        """
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    rows = conn.execute(
                        """
                        SELECT json_extract(metadata, '$.intent') as intent, COUNT(*) as count 
                        FROM usage_events 
                        WHERE event_type = 'ai_command_executed' 
                        GROUP BY intent 
                        ORDER BY count DESC 
                        LIMIT 5
                        """
                    ).fetchall()
                    return [{"intent": r[0], "count": r[1]} for r in rows if r[0]]
            except Exception as e:
                logger.error(f"PatternAnalyzer: Failed to analyze intents: {e}")
                return []

pattern_analyzer = PatternAnalyzer()
