import json
import uuid
import logging
from typing import List, Optional
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .models import UserMemoryMilestone

logger = logging.getLogger(__name__)

class UserMemoryTimelineManager:
    """
    Manages the chronological evolution timeline for each user.
    Tracks milestones like account creation, first login, feature exploration, etc.
    """

    def record_milestone(self, user_id: str, milestone_type: str, description: str, metadata: dict = None):
        """Records a new milestone in the user's timeline."""
        milestone = UserMemoryMilestone(
            id=str(uuid.uuid4()),
            user_id=user_id,
            milestone_type=milestone_type,
            description=description,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO user_memory_timeline (id, user_id, milestone_type, description, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (milestone.id, milestone.user_id, milestone.milestone_type, milestone.description,
                     milestone.timestamp.isoformat(), json.dumps(milestone.metadata))
                )
                conn.commit()
        
        logger.info(f"Milestone recorded for user {user_id}: {milestone_type}")
        return milestone

    def get_timeline(self, user_id: str) -> List[UserMemoryMilestone]:
        """Retrieves the full timeline for a user."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM user_memory_timeline WHERE user_id = ? ORDER BY timestamp ASC",
                    (user_id,)
                ).fetchall()
                
                return [UserMemoryMilestone(
                    id=row["id"],
                    user_id=row["user_id"],
                    milestone_type=row["milestone_type"],
                    description=row["description"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                ) for row in rows]

timeline_manager = UserMemoryTimelineManager()
