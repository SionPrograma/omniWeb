import logging
import json
import os
from typing import Dict, Any, List, Optional
import contextvars
from contextlib import contextmanager
from datetime import datetime

logger = logging.getLogger(__name__)

# --- Capability Constants (Phase 20) ---
STORAGE_READ = "storage_read"
STORAGE_WRITE = "storage_write"
NETWORK_ACCESS = "network_access"
AUDIO_INPUT = "audio_input"
AUDIO_OUTPUT = "audio_output"
VIDEO_INPUT = "video_input"
USER_LOGBOOK_ACCESS = "user_logbook_access"
USER_GRAPH_ACCESS = "user_graph_access"

# Creator-Only Capabilities
CREATOR_TOOLS_ACCESS = "creator_tools_access"
SYSTEM_STATE_ACCESS = "system_state_access"
CHIP_GENERATION_ACCESS = "chip_generation_access"
SYSTEM_PATCH_ACCESS = "system_patch_access"

# Admin-Level Capabilities (Phase 22)
ADMIN_OPS_ACCESS = "admin_ops_access"
ADMIN_LOGBOOK_ACCESS = "admin_logbook_access"

# Governance Capabilities (Phase 29)
BETA_TESTER_ACCESS = "beta_tester_access"
ADMIN_CANDIDATE_ACCESS = "admin_candidate_access"
GOVERNANCE_ADVISOR_ACCESS = "governance_advisor_access"

CREATOR_ONLY_PERMS = {
    CREATOR_TOOLS_ACCESS,
    SYSTEM_STATE_ACCESS,
    CHIP_GENERATION_ACCESS,
    SYSTEM_PATCH_ACCESS,
    GOVERNANCE_ADVISOR_ACCESS
}

ADMIN_PERMS = {
    ADMIN_OPS_ACCESS,
    ADMIN_LOGBOOK_ACCESS,
    ADMIN_CANDIDATE_ACCESS
}

BETA_PERMS = {
    BETA_TESTER_ACCESS
}

class PermissionDeniedError(Exception):
    """Exception thrown when a chip attempts an unauthorized action."""
    pass

# Context variable to store current context info
# We'll store a dict with 'chip_slug' and optionally 'user_id'
_current_ctx_info : contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar(
    "ctx_info",
    default={"chip_slug": None, "user_id": None},
)

_current_chip_ctx =  _current_ctx_info
@contextmanager
def set_chip_context(slug: str, user_id: Optional[str] = None):
    """
    Context manager to set the current executing chip slug and user globally.
    """
    token = _current_ctx_info.set({"chip_slug": slug, "user_id": user_id})
    try:
        yield
    finally:
        _current_ctx_info.reset(token)

def get_current_chip() -> Optional[str]:
    """Returns the currently active chip slug."""
    return _current_ctx_info.get()["chip_slug"]

def get_current_user_id() -> Optional[str]:
    """Returns the currently active user ID."""
    return _current_ctx_info.get()["user_id"]

def enforce_permission(required_permission: str):
    """
    Verifies that the current chip/context has the required permission.
    Denies access and logs if unauthorized.
    """
    ctx = _current_ctx_info.get()
    chip_slug = ctx["chip_slug"]
    user_id = ctx["user_id"] or "system"
    
    # 0. System Mode Enforcement (Phase 23)
    # We use direct DB check to avoid circular dependencies with creator_control_manager
    from backend.core.system_state.models import SystemMode
    from backend.core.config import settings
    from backend.core.database import db_manager
    
    system_mode = SystemMode.LIVE
    try:
        # Fast direct check
        with db_manager.get_connection(internal=True) as conn:
            row = conn.execute("SELECT value FROM system_governance WHERE key = 'system_mode'").fetchone()
            if row:
                system_mode = SystemMode(row["value"])
    except:
        pass # Fallback to LIVE if DB not ready
        
    is_creator = (str(user_id) == str(settings.CREATOR_ID))

    # 0. Creator Bypass (Phase 3: Hot Reload System)
    # The Creator has absolute authority over all chips and core systems.
    if is_creator:
        return True

    if system_mode == SystemMode.LOCKDOWN:
        if not is_creator and chip_slug != "core":
            logger.critical(f"LOCKDOWN BLOCKED: User {user_id} attempted {required_permission}")
            raise PermissionDeniedError("System is in LOCKDOWN mode. Only the Creator has access.")
            
    if system_mode == SystemMode.READ_ONLY:
        write_perms = {STORAGE_WRITE, "db_access", CHIP_GENERATION_ACCESS, SYSTEM_PATCH_ACCESS}
        if required_permission in write_perms and not is_creator:
            logger.warning(f"READ_ONLY BLOCKED: User {user_id} attempted {required_permission}")
            raise PermissionDeniedError("System is in READ_ONLY mode. Write operations are restricted.")

    # 1. Core system bypass
    if chip_slug == "core":
        return

    # 2. Untrusted check
    if not chip_slug:
        _log_denial("untrusted", user_id, required_permission)
        raise PermissionDeniedError(f"Untrusted context. Access to '{required_permission}' denied.")

    # 3. Resolve metadata
    from backend.core.module_registry import module_registry
    chip_info = module_registry.modules.get(chip_slug)
    
    metadata = {}
    if not chip_info:
        # Load from disk if not in memory (init-time)
        chip_json_path = f"chips/chip-{chip_slug}/chip.json"
        if os.path.exists(chip_json_path):
            try:
                with open(chip_json_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            except: pass
    else:
        metadata = chip_info.get("metadata", {})

    # 4. Check Permission List
    has_perm = check_permission(metadata, required_permission)
    
    # 5. Role-Based Hierarchy Check (Phase 22 & 29)
    # Placeholder for Admin IDs - in a real system this would be a DB check
    # For now, let's treat the Creator as a Super-Admin
    is_admin = is_creator or (user_id in ["admin_1", "admin_2"])
    is_admin_candidate = is_admin or (user_id in ["candidate_1"])
    is_beta_tester = is_admin_candidate or (user_id in ["tester_1"])

    if required_permission in CREATOR_ONLY_PERMS:
        if not is_creator:
            has_perm = False
            logger.warning(f"Creator-only permission '{required_permission}' denied for user '{user_id}'")
    
    elif required_permission in ADMIN_PERMS:
        if not is_admin:
            has_perm = False
            logger.warning(f"Admin-level permission '{required_permission}' denied for user '{user_id}'")
            
    elif required_permission in BETA_PERMS:
        if not is_beta_tester:
            has_perm = False
            logger.warning(f"Beta-level permission '{required_permission}' denied for user '{user_id}'")

    if not has_perm:
        _log_denial(chip_slug, user_id, required_permission)
        raise PermissionDeniedError(f"Permission '{required_permission}' denied for chip '{chip_slug}'.")

def check_permission(chip_metadata: Dict[str, Any], required_permission: str) -> bool:
    """Checks if permission is declared in metadata."""
    permissions = chip_metadata.get("permissions", [])
    if not isinstance(permissions, list):
        return False
    return required_permission in permissions

def _log_denial(chip_slug: str, user_id: str, permission: str):
    """Records security denial in database."""
    logger.error(f"SECURITY DENIAL: Chip '{chip_slug}' (User: {user_id}) requested '{permission}'")
    
    # Delayed import to avoid circular dependency
    try:
        from backend.core.security.manager import security_fortress
        security_fortress.log_creator_action(
            creator_id=user_id if user_id != "system" else "00000000-0000-0000-0000-000000000000",
            action_type="PERMISSION_DENIED",
            target=chip_slug,
            payload={"requested": permission, "result": "denied"}
        )
    except Exception as e:
        logger.warning(f"Failed to log security denial to DB: {e}")

def get_chip_permissions(chip_metadata: Dict[str, Any]) -> List[str]:
    return chip_metadata.get("permissions", [])