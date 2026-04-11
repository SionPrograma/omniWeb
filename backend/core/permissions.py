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

# --- System/Headless Task Config (Phase 127) ---
SYSTEM_TASK_PREFIX = "system:"
TRUSTED_SYSTEM_MODULES = {
    "core",
    "monitor",
    "governance",
    "integrity",
    "stability",
    "orchestration",
    "background_processor",
    "semantic_layer",
    "idea_cloud"
}

# Permissions allowed for trusted system tasks without a human user
ALLOWED_SYSTEM_PERMS = {
    "db_access",
    STORAGE_READ,
    STORAGE_WRITE,
    NETWORK_ACCESS,
    USER_LOGBOOK_ACCESS, # For automated auditing
    ADMIN_LOGBOOK_ACCESS
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
    If user_id is not provided, it inherits the one from the parent context.
    """
    current_ctx = _current_ctx_info.get()
    
    # Inherit existing user_id if not explicitly provided
    # This prevents inner context blocks from nuking the authenticated session
    effective_user_id = user_id if user_id is not None else current_ctx.get("user_id")
    
    token = _current_ctx_info.set({"chip_slug": slug, "user_id": effective_user_id})
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

    # 1. Core/Trusted system bypass
    # 'core' and trusted system modules (when called with system: prefix) are allowed full internal access.
    if chip_slug == "core":
        return

    # 1b. Headless Security Context (Phase 127)
    # Allows trusted background tasks to operate without a human user.
    if chip_slug and (chip_slug.startswith(SYSTEM_TASK_PREFIX) or chip_slug in TRUSTED_SYSTEM_MODULES):
        clean_slug = chip_slug[len(SYSTEM_TASK_PREFIX):] if chip_slug.startswith(SYSTEM_TASK_PREFIX) else chip_slug
        if clean_slug in TRUSTED_SYSTEM_MODULES:
            if required_permission in ALLOWED_SYSTEM_PERMS:
                return
            else:
                logger.warning(f"SYSTEM RESTRICTION: Trusted task '{chip_slug}' attempted unallowed perm '{required_permission}'")
        else:
            logger.warning(f"UNTRUSTED SYSTEM TASK: '{chip_slug}' is not in trusted module list.")

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

    # 5. Resolve Mode-Based Permission (OMNI_MODE_ARCHITECTURE_V1.0)
    from backend.core.governance.mode_registry import ModeRegistry, OmniMode, ModePermission
    
    # Resolve the active mode for the user
    user_mode = OmniMode.PUBLIC
    if is_creator:
        user_mode = OmniMode.CREATOR
    elif user_id and user_id != "system":
        # Resolve mode from DB
        try:
            with db_manager.get_connection(internal=True) as conn:
                row = conn.execute("SELECT username, role, mode FROM users WHERE id = ?", (user_id,)).fetchone()
                if row:
                    from backend.core.auth import OmniUser
                    user_mode = OmniUser.resolve_mode(row["username"], row["role"], row["mode"])
        except:
            pass

    # Default to DENIED if not a trusted core module (Shift to Deny-by-Default V1.5)
    has_perm = False
    
    # Core/Trusted Bypass Redux (Consistency Check)
    if is_creator or chip_slug == "core":
        has_perm = True

    # Map legacy permission strings to ModePermissions if possible
    # (Harden known sensitive surfaces)
    perm_map = {
        CREATOR_TOOLS_ACCESS: ModePermission.SYSTEM_MAINTENANCE,
        ADMIN_OPS_ACCESS: ModePermission.SYSTEM_MAINTENANCE,
        GOVERNANCE_ADVISOR_ACCESS: ModePermission.GOVERNANCE_VIEW,
    }
    
    if required_permission in perm_map:
        if ModeRegistry.has_permission(user_mode, perm_map[required_permission]):
            has_perm = True
        else:
            logger.warning(f"MODE REJECTION: User {user_id} ({user_mode}) denied {required_permission}")
            has_perm = False
    
    # Final overrides and strict blocks
    if required_permission in CREATOR_ONLY_PERMS and user_mode != OmniMode.CREATOR:
        has_perm = False
    
    if not has_perm:
        if required_permission in ADMIN_PERMS and user_mode in [OmniMode.CREATOR, OmniMode.ADMIN]:
             has_perm = True
        if required_permission in BETA_PERMS and user_mode in [OmniMode.CREATOR, OmniMode.ADMIN, OmniMode.TESTER]:
             has_perm = True
    
    # Strict Lockdown Enforcement
    from backend.core.system_state.models import SystemMode
    # system_mode resolved earlier at line 125
    if system_mode == SystemMode.LOCKDOWN and not is_creator and chip_slug != "core":
        has_perm = False

    if not has_perm:
        # Phase 1: Modular Sovereignty Bridge
        # Check if the currently executing chip has specifically declared this 
        # capability in its signed metadata (chip.json).
        if metadata and check_permission(metadata, required_permission):
            logger.debug(f"MODULAR PERMIT: Chip '{chip_slug}' authorized for '{required_permission}' via metadata.")
            has_perm = True

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
    """Records security denial in database with surgical error handling."""
    logger.error(f"SECURITY DENIAL: Chip '{chip_slug}' (User: {user_id or 'system'}) requested '{permission}'")
    
    # Delayed import to avoid circular dependency
    try:
        from backend.core.security.manager import security_fortress
        effective_user = user_id if user_id and user_id != "system" else "00000000-0000-0000-0000-000000000000"
        
        security_fortress.log_creator_action(
            creator_id=effective_user,
            action_type="PERMISSION_DENIED",
            target=chip_slug,
            payload={"requested": permission, "result": "denied", "fallback_id_used": user_id is None or user_id == "system"}
        )
        logger.debug(f"SECURITY AUDIT: Persistence successful for {chip_slug} denial.")
    except Exception as e:
        # Phase 0: Surgical Reporting of Persistence Failures
        error_msg = str(e)
        if "FOREIGN KEY constraint failed" in error_msg:
            logger.warning(f"SECURITY AUDIT FAILED (FK): Could not persist denial for '{chip_slug}'. Likely missing 'system' user in DB. Error: {error_msg}")
        else:
            logger.warning(f"SECURITY AUDIT FAILED: Unknown error persisting denial for '{chip_slug}': {error_msg}")
        
        # We DO NOT re-raise; the denial (the core logic) is already done.
        logger.info(f"FALLBACK: Denial logged to STDOUT but NOT persisted to DB.")

def get_chip_permissions(chip_metadata: Dict[str, Any]) -> List[str]:
    return chip_metadata.get("permissions", [])