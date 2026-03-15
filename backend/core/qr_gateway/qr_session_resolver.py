import logging
from typing import Optional
from backend.core.auth import create_session, get_user_by_username
from .qr_token_manager import qr_token_manager

logger = logging.getLogger(__name__)

class QRSessionResolver:
    """
    Resolves a validated QR token into a full OmniWeb session.
    Automatically maps roles to dynamic or static users.
    """
    
    async def resolve_session(self, token_str: str) -> Optional[str]:
        """
        Validates the token and creates a session for the associated role.
        Returns the session token (JWT alternative in OmniWeb).
        """
        qr_token = qr_token_manager.validate_token(token_str)
        if not qr_token:
            logger.warning(f"QR Access Refused: Invalid or expired token {token_str}")
            return None
            
        # Map role to user
        # In a real system, we might create a transient user or use a role-based template
        username_map = {
            "creator": "creator",
            "admin": "admin",
            "admin_candidate": "onboarding_user",
            "beta_tester": "beta_tester",
            "public": "public_guest"
        }
        
        username = username_map.get(qr_token.role, "guest")
        
        # In OmniWeb, users are stored in the DB. Ensure the user exists or fallback to admin if matching.
        # For simplicity in this gateway pass, we create a session for the user ID if found.
        user = get_user_by_username(username)
        if not user:
            # Fallback logic: check if it's the admin role and settings.ADMIN_TOKEN is used
            # For now, we assume users are pre-seeded via migrations (e.g. from previous sessions)
            logger.error(f"User '{username}' not found for role mapping. Access denied.")
            return None
            
        # Create standard platform session
        session_token = create_session(user.id)
        
        # Mark QR token as used
        qr_token_manager.mark_used(token_str)
        
        logger.info(f"QR Access Success: User '{username}' authenticated via QR.")
        return session_token

qr_session_resolver = QRSessionResolver()
