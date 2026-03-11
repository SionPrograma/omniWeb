import logging
import json
from datetime import datetime
from typing import Dict, Any, List
from .usage_models import UsageEvent
from backend.core.database import db_manager

logger = logging.getLogger(__name__)

class UsageTracker:
    """
    Captures and persists system usage events for the Self-Improvement Engine.
    """
    def log_event(self, event_type: str, chip_slug: str = None, user_session: str = None, metadata: Dict[str, Any] = None):
        """
        Logs a usage event to the database.
        """
        from backend.core.permissions import set_chip_context
        event = UsageEvent(
            event_type=event_type,
            chip_slug=chip_slug,
            user_session=user_session,
            metadata=metadata or {}
        )
        
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute(
                        """
                        INSERT INTO usage_events (event_type, chip_slug, user_session, metadata, timestamp)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            event.event_type,
                            event.chip_slug,
                            event.user_session,
                            json.dumps(event.metadata),
                            event.timestamp.isoformat()
                        )
                    )
                    conn.commit()
            logger.debug(f"Usage tracked: {event.event_type} on {event.chip_slug or 'system'}")
        except Exception as e:
            logger.error(f"Failed to track usage event: {e}")

    def get_statistics(self) -> Dict[str, Any]:
        """
        Computes system usage statistics.
        """
        stats = {
            "top_chips": [],
            "event_distribution": {},
            "total_events": 0
        }
        
        try:
            with db_manager.get_connection() as conn:
                # Total events
                stats["total_events"] = conn.execute("SELECT COUNT(*) FROM usage_events").fetchone()[0]
                
                # Top chips
                rows = conn.execute(
                    "SELECT chip_slug, COUNT(*) as count FROM usage_events WHERE chip_slug IS NOT NULL GROUP BY chip_slug ORDER BY count DESC LIMIT 5"
                ).fetchall()
                stats["top_chips"] = [{"slug": r[0], "count": r[1]} for r in rows]
                
                # Event types
                rows = conn.execute(
                    "SELECT event_type, COUNT(*) as count FROM usage_events GROUP BY event_type"
                ).fetchall()
                stats["event_distribution"] = {r[0]: r[1] for r in rows}
                
        except Exception as e:
            logger.error(f"Failed to fetch usage statistics: {e}")
            
        return stats

usage_tracker = UsageTracker()
