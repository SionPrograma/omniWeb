import logging
import json
from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.ai_host.memory.mission_telemetry import mission_telemetry

logger = logging.getLogger(__name__)

class LockType(str, Enum):
    WRITE = "WRITE"
    READ = "READ"
    EXCLUSIVE = "EXCLUSIVE"

class LockStatus(str, Enum):
    ACQUIRED = "ACQUIRED"
    RELEASED = "RELEASED"
    WAITING = "WAITING"

class ResourceLock(BaseModel):
    resource_key: str
    mission_id: str
    lock_type: LockType = LockType.WRITE
    status: LockStatus = LockStatus.ACQUIRED
    reason: Optional[str] = None
    acquired_at: datetime = Field(default_factory=datetime.now)
    released_at: Optional[datetime] = None

class ResourceLockManager:
    """
    Governance Layer for Resource Locking between Parallel Missions.
    Prevents race conditions and file collisions.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ResourceLockManager, cls).__new__(cls)
            cls._instance._ensure_table()
            cls._instance.reconcile_locks()
        return cls._instance

    def reconcile_locks(self):
        """
        Critical Recovery: Reconciles locks with mission states.
        Releases any lock held by a mission that is no longer OPEN or PAUSED.
        Ensures continuity after a cold restart or crash.
        """
        logger.info("[RESOURCE_LOCK] Reconciling locks with current mission states...")
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Find locks for missions that are NOT in active status
                # Or locks for missions that simply don't exist anymore
                query = """
                UPDATE system_locks 
                SET status = 'RELEASED', released_at = ?
                WHERE status = 'ACQUIRED' AND mission_id NOT IN (
                    SELECT mission_id FROM system_missions WHERE status IN ('OPEN', 'PAUSED')
                )
                """
                cursor = conn.execute(query, (datetime.now().isoformat(),))
                if cursor.rowcount > 0:
                    logger.warning(f"[RESOURCE_LOCK] Cleaned up {cursor.rowcount} orphan/zombie locks.")
                conn.commit()

    def _ensure_table(self):
        """Ensures the system_locks table exists with the correct schema."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS system_locks (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        resource_key TEXT UNIQUE NOT NULL,
                        mission_id TEXT NOT NULL,
                        lock_type TEXT DEFAULT 'WRITE',
                        status TEXT DEFAULT 'ACQUIRED',
                        reason TEXT,
                        acquired_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        released_at DATETIME
                    )
                """)
                conn.commit()

    def acquire_lock(self, resource_key: str, mission_id: str, lock_type: LockType = LockType.WRITE, reason: str = "") -> bool:
        """
        Attempts to acquire a lock on a resource.
        Returns True if successful, False otherwise.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # 1. Check if resource is already locked by another mission
                row = conn.execute(
                    "SELECT * FROM system_locks WHERE resource_key = ? AND status = ?", 
                    (resource_key, LockStatus.ACQUIRED.value)
                ).fetchone()

                if row:
                    if row['mission_id'] == mission_id:
                        # Already owned by this mission
                        return True
                    else:
                        logger.warning(f"[RESOURCE_LOCK] Conflict: {resource_key} is locked by {row['mission_id']}")
                        return False

                # 2. Acquire lock
                try:
                    conn.execute("""
                        INSERT OR REPLACE INTO system_locks 
                        (resource_key, mission_id, lock_type, status, reason, acquired_at, released_at)
                        VALUES (?, ?, ?, ?, ?, ?, NULL)
                    """, (
                        resource_key, mission_id, lock_type.value, LockStatus.ACQUIRED.value, reason, datetime.now().isoformat()
                    ))
                    conn.commit()
                    logger.info(f"[RESOURCE_LOCK] Acquired: {resource_key} for mission {mission_id}")
                    
                    # Telemetry (Phase: AUDIT OVERLAY)
                    mission_telemetry.record_event(
                        mission_id, "lock_acquired", 
                        f"Recurso bloqueado: {resource_key}", 
                        details={"resource": resource_key, "type": lock_type.value, "reason": reason},
                        source_actor="ResourceLockManager"
                    )
                    return True
                except Exception as e:
                    logger.error(f"[RESOURCE_LOCK] Error acquiring lock: {e}")
                    return False

    def release_lock(self, resource_key: str, mission_id: str):
        """Mark a lock as released."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE system_locks SET status = ?, released_at = ? WHERE resource_key = ? AND mission_id = ?",
                    (LockStatus.RELEASED.value, datetime.now().isoformat(), resource_key, mission_id)
                )
                conn.commit()
                logger.info(f"[RESOURCE_LOCK] Released: {resource_key} by mission {mission_id}")
                
                # Telemetry (Phase: AUDIT OVERLAY)
                mission_telemetry.record_event(
                    mission_id, "lock_released", 
                    f"Recurso liberado: {resource_key}", 
                    details={"resource": resource_key},
                    source_actor="ResourceLockManager"
                )

    def release_all_for_mission(self, mission_id: str):
        """Releases all locks held by a specific mission."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    "UPDATE system_locks SET status = ?, released_at = ? WHERE mission_id = ? AND status = ?",
                    (LockStatus.RELEASED.value, datetime.now().isoformat(), mission_id, LockStatus.ACQUIRED.value)
                )
                conn.commit()
                logger.info(f"[RESOURCE_LOCK] Released all locks for mission {mission_id}")

    def get_locks_for_mission(self, mission_id: str) -> List[Dict[str, Any]]:
        """Returns all active locks for a mission."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM system_locks WHERE mission_id = ? AND status = ?",
                    (mission_id, LockStatus.ACQUIRED.value)
                ).fetchall()
                return [dict(r) for r in rows]

    def get_all_active_locks(self) -> List[Dict[str, Any]]:
        """Returns all active locks in the system."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM system_locks WHERE status = ?",
                    (LockStatus.ACQUIRED.value,)
                ).fetchall()
                return [dict(r) for r in rows]

    def check_conflict(self, resource_keys: List[str], mission_id: str) -> Optional[Dict[str, Any]]:
        """
        Checks if any of the requested resources are locked by another mission.
        Returns the first conflicting lock info if any, else None.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                for rk in resource_keys:
                    row = conn.execute(
                        "SELECT * FROM system_locks WHERE resource_key = ? AND status = ? AND mission_id != ?",
                        (rk, LockStatus.ACQUIRED.value, mission_id)
                    ).fetchone()
                    if row:
                        return dict(row)
        return None

resource_lock_manager = ResourceLockManager()
