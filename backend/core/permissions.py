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

CREATOR_ONLY_PERMS = {
    CREATOR_TOOLS_ACCESS,
    SYSTEM_STATE_ACCESS,
    CHIP_GENERATION_ACCESS,
    SYSTEM_PATCH_ACCESS
}

class PermissionDeniedError(Exception):
    """Exception thrown when a chip attempts an unauthorized action."""
    pass

# Context variable to store current context info
# We'll store a dict with 'chip_slug' and optionally 'user_id'
_current_ctx_info: contextvars.ContextVar[Dict[str, Any]] = contextvars.ContextVar("ctx_info", default={"chip_slug": None, "user_id": None})

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
    
    # 5. Creator check for sensitive perms
    if has_perm and required_permission in CREATOR_ONLY_PERMS:
        # Must verify user is creator
        from backend.core.config import settings
        if user_id != settings.CREATOR_ID:
            has_perm = False
            logger.warning(f"Creator-only permission '{required_permission}' denied for non-creator user '{user_id}'")

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
