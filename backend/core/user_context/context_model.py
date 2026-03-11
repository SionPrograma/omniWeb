import logging
import json
from datetime import datetime
from typing import List, Dict, Any
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class ContextModel:
    """
    Core engine for managing and persisting user behavioral models.
    """
    def save_pattern(self, pattern_type: str, pattern_data: Dict[str, Any], confidence: float):
        """
        Saves or updates a behavioral pattern.
        """
        data_json = json.dumps(pattern_data)
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    # Check for existing similar pattern
                    exists = conn.execute(
                        "SELECT id, confidence FROM user_behavior_patterns WHERE pattern_type = ? AND pattern_data = ?",
                        (pattern_type, data_json)
                    ).fetchone()
                    
                    if exists:
                        # Update confidence and timestamp
                        new_confidence = min(1.0, exists["confidence"] + confidence)
                        conn.execute(
                            "UPDATE user_behavior_patterns SET confidence = ?, last_seen = CURRENT_TIMESTAMP WHERE id = ?",
                            (new_confidence, exists["id"])
                        )
                    else:
                        conn.execute(
                            "INSERT INTO user_behavior_patterns (pattern_type, pattern_data, confidence) VALUES (?, ?, ?)",
                            (pattern_type, data_json, confidence)
                        )
                    conn.commit()
            except Exception as e:
                logger.error(f"ContextModel: Failed to save pattern: {e}")

    def get_patterns(self, pattern_type: str = None) -> List[Dict[str, Any]]:
        """
        Retrieves all behavioral patterns, optionally filtered by type.
        """
        query = "SELECT pattern_type, pattern_data, confidence FROM user_behavior_patterns"
        params = ()
        if pattern_type:
            query += " WHERE pattern_type = ?"
            params = (pattern_type,)
            
        with set_chip_context("core"):
            try:
                with db_manager.get_connection() as conn:
                    rows = conn.execute(query, params).fetchall()
                    return [
                        {
                            "type": r["pattern_type"],
                            "data": json.loads(r["pattern_data"]),
                            "confidence": r["confidence"]
                        }
                        for r in rows
                    ]
            except Exception as e:
                logger.error(f"ContextModel: Failed to fetch patterns: {e}")
                return []

context_model = ContextModel()
