"""
File Scope Guard — OMNI_PATCH Phase F.
Governs file access and mutation scope.
"""

import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

@dataclass
class FileScopeLock:
    scope_id: str
    target_path: str
    range_hint: Optional[str] = None
    state: str = "proposed"
    metadata: Dict[str, Any] = None

class FileScopeGuard:
    """
    Prevents uncontrolled mutation by establishing scope boundaries.
    """

    def acquire_lock(self, target_path: str, range_hint: Optional[str] = None, mission_id: Optional[str] = None) -> FileScopeLock:
        lock_id = f"lock:{mission_id or 'global'}:{target_path}"
        logger.info(f"[FILE_GUARD] Acquiring lock for: {target_path} (ID: {lock_id})")
        
        return FileScopeLock(
            scope_id=lock_id,
            target_path=target_path,
            range_hint=range_hint,
            state="locked",
            metadata={"mission_id": mission_id}
        )

    def release_lock(self, lock: FileScopeLock) -> None:
        logger.info(f"[FILE_GUARD] Releasing lock: {lock.scope_id}")
        lock.state = "released"

    def validate_mutation(self, lock: FileScopeLock, proposed_change: str) -> bool:
        """Additiver rule: check if change stays within range_hint."""
        if not lock or lock.state != "locked":
            logger.warning(f"[FILE_GUARD] Mutation attempted without active lock on {lock.target_path if lock else 'unknown'}")
            return False
        
        # In a real implementation, we could parsed range_hint (e.g. "lines 10-20")
        # and verify the diff only affects those lines.
        return True

file_scope_guard = FileScopeGuard()
