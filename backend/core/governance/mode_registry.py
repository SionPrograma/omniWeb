from enum import Enum
from typing import Dict, List, Set, Any

class OmniMode(str, Enum):
    CREATOR = "CREATOR"
    ADMIN = "ADMIN"
    TESTER = "TESTER"
    PUBLIC = "PUBLIC"

class ModePermission(str, Enum):
    GOVERNANCE_EXECUTE = "governance:execute" # Rollback, Apply, Approve
    GOVERNANCE_VIEW = "governance:view"       # View Dashboard, Ledger
    EVIDENCE_INSPECT = "evidence:inspect"    # Atlas Detail
    PULSE_MANAGE = "pulse:manage"            # Dismiss, Acknowledge
    SYSTEM_MAINTENANCE = "system:maintenance" # Logs, Settings
    PUBLIC_OUTPUT = "public:output"          # Safe results

class VisibilityLevel(str, Enum):
    FULL = "FULL"
    READ_ONLY = "READ_ONLY"
    MASKED = "MASKED"
    HIDDEN = "HIDDEN"

class ModeRegistry:
    """
    OMNIWEB — BLOQUE: OMNI_MODE_ARCHITECTURE_V1.0.
    Centralized mapping of Modes to Permissions.
    """
    
    PERMISSIONS: Dict[OmniMode, Set[ModePermission]] = {
        OmniMode.CREATOR: {
            ModePermission.GOVERNANCE_EXECUTE,
            ModePermission.GOVERNANCE_VIEW,
            ModePermission.EVIDENCE_INSPECT,
            ModePermission.PULSE_MANAGE,
            ModePermission.SYSTEM_MAINTENANCE,
            ModePermission.PUBLIC_OUTPUT
        },
        OmniMode.ADMIN: {
            ModePermission.GOVERNANCE_VIEW,
            ModePermission.EVIDENCE_INSPECT,
            ModePermission.PULSE_MANAGE,
            ModePermission.SYSTEM_MAINTENANCE,
            ModePermission.PUBLIC_OUTPUT
        },
        OmniMode.TESTER: {
            ModePermission.GOVERNANCE_VIEW,
            ModePermission.EVIDENCE_INSPECT,
            ModePermission.PUBLIC_OUTPUT
        },
        OmniMode.PUBLIC: {
            ModePermission.PUBLIC_OUTPUT
        }
    }

    @classmethod
    def has_permission(cls, mode: OmniMode, permission: ModePermission) -> bool:
        return permission in cls.PERMISSIONS.get(mode, set())

    @classmethod
    def get_visibility(cls, mode: OmniMode, surface: str) -> VisibilityLevel:
        """
        V1.1: Surface visibility map.
        """
        mapping = {
            "governance_dashboard": {
                OmniMode.CREATOR: VisibilityLevel.FULL,
                OmniMode.ADMIN: VisibilityLevel.FULL,
                OmniMode.TESTER: VisibilityLevel.READ_ONLY,
                OmniMode.PUBLIC: VisibilityLevel.HIDDEN
            },
            "catalyst_traces": {
                OmniMode.CREATOR: VisibilityLevel.FULL,
                OmniMode.ADMIN: VisibilityLevel.FULL,
                OmniMode.TESTER: VisibilityLevel.MASKED,
                OmniMode.PUBLIC: VisibilityLevel.HIDDEN
            }
        }
        return mapping.get(surface, {}).get(mode, VisibilityLevel.HIDDEN)

    @classmethod
    def mask_data(cls, data: Any, mode: OmniMode, surface: str) -> Any:
        """
        Redacts sensitive fields for MASKED or HIDDEN surfaces.
        """
        vis = cls.get_visibility(mode, surface)
        if vis == VisibilityLevel.HIDDEN: return None
        if vis == VisibilityLevel.FULL or vis == VisibilityLevel.READ_ONLY: return data
        
        # MASKED logic: Redact specific sensitive keys
        sensitive_keys = {"raw", "raw_payload", "evidence_refs", "raw_log"}
        if isinstance(data, list):
            return [cls.mask_data(item, mode, surface) for item in data]
        if isinstance(data, dict):
            return {k: ("[SENSITIVE_CONTENT_MASKED]" if k in sensitive_keys else v) for k, v in data.items()}
        return data

mode_registry = ModeRegistry()
