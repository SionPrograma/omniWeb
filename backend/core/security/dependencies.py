from fastapi import Security, HTTPException, status, Header
from typing import Optional
from backend.core.auth import get_current_user, OmniUser
from backend.core.config import settings
from .manager import security_fortress

async def get_creator_user(
    current_user: OmniUser = Security(get_current_user),
    x_device_id: Optional[str] = Header(None),
    x_device_signature: Optional[str] = Header(None),
    x_shell_identity: Optional[str] = Header(None)
) -> OmniUser:
    """
    Security Gateway for Creator endpoints.
    Enforces Creator ID match and Device Trust.
    Allows authenticated shell sessions to bypass device metadata.
    """
    # 1. Identity Check
    if current_user.id != settings.CREATOR_ID:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access Denied: High Security Creator Authorization Required."
        )

    # 2. Shell Identity Bypass
    # If the request comes from the authenticated OmniWeb Shell, 
    # we allow the bypass for the device trust metadata check.
    if x_shell_identity == "omniweb-shell":
        return current_user

    # 3. Device Trust Check (Enforced for non-shell or external API calls)
    if settings.REQUIRE_TRUSTED_DEVICE:
        if not x_device_id or not x_device_signature:
            raise HTTPException(
                status_code=status.HTTP_412_PRECONDITION_FAILED,
                detail="Security Violation: Missing Device Trust Metadata."
            )
            
        if not security_fortress.is_device_trusted(current_user.id, x_device_id, x_device_signature):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Security Violation: Device not trusted for Creator access."
            )

    # 3. Hardware Auth Check (Placeholder for real WebAuthn flow)
    if settings.REQUIRE_HARDWARE_AUTH:
        # Hardware auth usually requires a challenge-response flow
        # In V1 we enforce that the user must have 'fido2_verified' in their current session session scope
        # (Mocked for this phase)
        pass

    return current_user
