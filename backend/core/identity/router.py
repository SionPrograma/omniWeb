from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import RedirectResponse
from .oauth_manager import oauth_manager
from .session_manager import identity_session_manager
from .models import SessionInfo
from backend.core.auth import get_current_user, OmniUser
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/login/{provider}")
async def login(provider: str, redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"):
    """
    Redirects user to the OAuth provider login page.
    """
    if provider not in oauth_manager.providers:
        raise HTTPException(status_code=400, detail=f"Provider {provider} not supported.")
    
    state = oauth_manager.generate_state(provider)
    auth_url = oauth_manager.providers[provider].get_login_url(redirect_uri, state)
    
    return {"login_url": auth_url, "state": state}

@router.get("/callback")
async def callback(code: str, state: str, redirect_uri: str = "http://localhost:8000/api/v1/auth/callback"):
    """
    Handles the redirect back from the OAuth provider.
    """
    provider_name = oauth_manager.verify_state(state)
    if not provider_name:
        raise HTTPException(status_code=400, detail="Invalid state parameter.")
        
    try:
        # 1. Exchange code for identity
        identity = await oauth_manager.handle_callback(provider_name, code, redirect_uri)
        
        # 2. Sync user and workspace
        internal_id = identity_session_manager.get_or_create_user(identity)
        
        # 3. Create session
        session = identity_session_manager.create_session(internal_id, identity)
        
        return {
            "status": "success",
            "message": "Authenticated successfully",
            "token": session.token,
            "user": session.identity
        }
    except Exception as e:
        logger.error(f"Auth callback failed: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed during callback processing.")

@router.get("/session")
async def get_session(current_user: OmniUser = Depends(get_current_user)):
    """
    Returns current session info.
    """
    return {
        "user_id": current_user.id,
        "username": current_user.username,
        "role": current_user.role,
        "is_active": current_user.is_active
    }

@router.post("/logout")
async def logout(request: Request):
    """
    Invalidates the current session.
    """
    # In a real JWT system, we might blacklist. 
    # Here we delete from sessions table.
    token = request.headers.get("Authorization")
    if token and token.startswith("Bearer "):
        token = token.split(" ")[1]
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
                conn.commit()
    
    return {"status": "success", "message": "Logged out"}
