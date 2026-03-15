import logging
import json
import asyncio
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.system_state.models import SystemMode
from backend.core.security.manager import security_fortress

logger = logging.getLogger(__name__)

class CreatorControlManager:
    """
    Handles global system governance, maintenance scheduling, and announcements.
    """
    
    def __init__(self):
        self._current_mode = SystemMode.LIVE
        self._active_announcement = None
        self._active_maintenance = None
        self._last_mode_check = 0

    @property
    def current_mode(self) -> SystemMode:
        """Synchronous access to the last known system mode."""
        return self._current_mode

    async def get_system_mode(self) -> SystemMode:
        """Retrieves current system mode from persistence."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute("SELECT value FROM system_governance WHERE key = 'system_mode'").fetchone()
                if row:
                    self._current_mode = SystemMode(row["value"])
                return self._current_mode

    async def set_system_mode(self, mode: SystemMode, creator_id: str):
        """Updates system mode and logs the action."""
        old_mode = await self.get_system_mode()
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO system_governance (key, value, updated_by, updated_at) VALUES (?, ?, ?, ?)",
                    ("system_mode", mode.value, creator_id, datetime.utcnow().isoformat())
                )
                conn.commit()
        
        self._current_mode = mode
        security_fortress.log_creator_action(
            creator_id=creator_id,
            action_type="SET_SYSTEM_MODE",
            target="system",
            payload={"old_mode": old_mode.value, "new_mode": mode.value}
        )
        logger.warning(f"SYSTEM MODE CHANGED: {old_mode} -> {mode} by {creator_id}")

    async def schedule_maintenance(self, start_time: str, duration_minutes: int, message: str, creator_id: str):
        """Schedules a maintenance window."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO maintenance_schedules (start_time, duration_minutes, message, creator_id, status)
                    VALUES (?, ?, ?, ?, 'SCHEDULED')
                    """,
                    (start_time, duration_minutes, message, creator_id)
                )
                conn.commit()
        
        security_fortress.log_creator_action(
            creator_id=creator_id,
            action_type="SCHEDULE_MAINTENANCE",
            target="maintenance",
            payload={"start_time": start_time, "duration": duration_minutes, "message": message}
        )

    async def get_active_maintenance(self) -> Optional[Dict[str, Any]]:
        """Checks for active or upcoming maintenance."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Find the next scheduled or currently active maintenance
                row = conn.execute(
                    "SELECT * FROM maintenance_schedules WHERE status IN ('SCHEDULED', 'ACTIVE') ORDER BY start_time ASC LIMIT 1"
                ).fetchone()
                
                if not row:
                    return None
                
                data = dict(row)
                # Check if it should be active
                start = datetime.fromisoformat(data["start_time"].replace('Z', '+00:00'))
                now = datetime.utcnow()
                
                if start <= now <= start + timedelta(minutes=data["duration_minutes"]):
                    if data["status"] == "SCHEDULED":
                        # Auto-activate
                        conn.execute("UPDATE maintenance_schedules SET status = 'ACTIVE' WHERE id = ?", (data["id"],))
                        conn.commit()
                        data["status"] = "ACTIVE"
                elif now > start + timedelta(minutes=data["duration_minutes"]):
                        # Auto-complete
                        conn.execute("UPDATE maintenance_schedules SET status = 'COMPLETED' WHERE id = ?", (data["id"],))
                        conn.commit()
                        return None
                
                return data

    async def publish_announcement(self, message: str, msg_type: str, creator_id: str, minutes_valid: int = 1440):
        """Publishes a global announcement."""
        expires_at = (datetime.utcnow() + timedelta(minutes=minutes_valid)).isoformat()
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE global_announcements SET is_active = 0 WHERE is_active = 1"
                ) # Deactivate previous
                conn.execute(
                    """
                    INSERT INTO global_announcements (message, type, creator_id, expires_at)
                    VALUES (?, ?, ?, ?)
                    """,
                    (message, msg_type, creator_id, expires_at)
                )
                conn.commit()
        
        security_fortress.log_creator_action(
            creator_id=creator_id,
            action_type="PUBLISH_ANNOUNCEMENT",
            target="announcement",
            payload={"message": message, "type": msg_type, "expires_at": expires_at}
        )

    async def get_active_announcement(self) -> Optional[Dict[str, Any]]:
        """Retrieves the current active global announcement."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                now = datetime.utcnow().isoformat()
                row = conn.execute(
                    "SELECT * FROM global_announcements WHERE is_active = 1 AND (expires_at IS NULL OR expires_at > ?) ORDER BY created_at DESC LIMIT 1",
                    (now,)
                ).fetchone()
                return dict(row) if row else None

    async def force_rollback(self, label: str, creator_id: str):
        """Forces a system-wide rollback to a named checkpoint."""
        # Requires integration with Admin's checkpoint system
        from backend.core.admin_logbook.manager import admin_logbook_manager
        
        security_fortress.log_creator_action(
            creator_id=creator_id,
            action_type="FORCE_ROLLBACK",
            target="system",
            payload={"checkpoint_label": label}
        )
        
        return await admin_logbook_manager.rollback_to_checkpoint(label, creator_id)

creator_control_manager = CreatorControlManager()
