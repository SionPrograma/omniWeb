from typing import List, Optional, Dict, Any
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
        
        # 2. Sync External Bridge to Sovereign Space (V1.0 Block 03)
        # identity['sub'] is the stable Google User ID
        from .space_registry import space_registry
        internal_id = space_registry.resolve_external_identity(provider_name, identity.get("sub", identity.get("id")))
        
        # 3. Create session with internal anchor
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

from .space_registry import space_registry
 
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
 
@router.get("/space")
async def get_personal_space(current_user: OmniUser = Depends(get_current_user)):
    """
    V1.0 Block 01: Personal Space Pulse.
    Resolves the active user's persistent identity to their governed Personal Space.
    """
    space = space_registry.resolve_space(current_user.id)
    return {
        "status": "success",
        "space": space.model_dump()
    }

@router.get("/spaces")
async def list_all_spaces(current_user: OmniUser = Depends(get_current_user)):
    """
    V1.0 Block 06: Space Inventory (Creator Only).
    """
    from backend.core.permissions import enforce_permission
    enforce_permission("creator_access")
    spaces = space_registry.list_all_spaces()
    return {
        "status": "success", 
        "spaces": [s.model_dump() for s in spaces]
    }

@router.get("/artifacts")
async def get_user_artifacts(current_user: OmniUser = Depends(get_current_user)):
    """
    V1.0 Block 02: Sovereign Result Retrieval.
    Lists all artifacts owned by the current user's Personal Space.
    """
    space = space_registry.resolve_space(current_user.id)
    artifacts = space_registry.get_artifacts_for_space(space.space_id)
    return {
        "status": "success",
        "artifacts": [a.model_dump() for a in artifacts]
    }

@router.get("/artifacts/{artifact_id}/content")
async def get_artifact_content(
    artifact_id: str, 
    current_user: OmniUser = Depends(get_current_user)
):
    """
    V1.0 Block 04: Secure Artifact content retrieval.
    Only allows access if the artifact belongs to the current user's space.
    """
    space = space_registry.resolve_space(current_user.id)
    content_data = space_registry.get_artifact_content(artifact_id, space.space_id)
    
    if not content_data:
         raise HTTPException(status_code=403, detail="Artifact access denied or missing.")
         
    return {
        "status": "success",
        "artifact": content_data
    }

from .connector_registry import connector_registry

@router.get("/connectors")
async def list_connectors(current_user: OmniUser = Depends(get_current_user)):
    """
    V1.0 Block 01: External App Governance Layer Pulse.
    Lists all governed connectors bound to the active user's Personal Space.
    """
    space = space_registry.resolve_space(current_user.id)
    connectors = connector_registry.get_connectors_for_space(space.space_id)
    return {
        "status": "success",
        "connectors": [c.model_dump() for c in connectors]
    }

@router.post("/connectors")
async def register_connector(
    connector_id: str,
    owner_space_id: str,
    provider_type: str,
    capability: str = "READ_ONLY",
    config: Dict[str, str] = {},
    current_user: OmniUser = Depends(get_current_user)
):
    """
    V1.0 Block 06: Manual Connector Registration.
    Persists a new governed connector bound to a specific Personal Space.
    """
    from backend.core.permissions import enforce_permission
    from .models import ExternalConnector, CapabilityClass
    enforce_permission("creator_access")
    
    conn = ExternalConnector(
        connector_id=connector_id,
        owner_space_id=owner_space_id,
        provider_type=provider_type,
        capability=CapabilityClass(capability),
        config=config
    )
    
    registered = connector_registry.register_connector(conn)
    return {
        "status": "success",
        "connector": registered.model_dump()
    }

from .connector_execution import governed_executor

@router.post("/connectors/execute")
async def execute_connector(
    connector_id: str, 
    action: str = "READ", 
    params: Dict[str, Any] = {},
    current_user: OmniUser = Depends(get_current_user)
):
    """
    V1.0 Block 02: Governed Tool Access Pulse.
    Executes a registered connector within the user's Personal Space boundary.
    """
    from typing import Dict, Any
    result = governed_executor.execute(current_user.id, connector_id, action, params)
    return {
        "status": result.status,
        "execution": result.model_dump()
    }

@router.patch("/connectors/{connector_id}/status")
async def update_connector_status(
    connector_id: str, 
    status: str, 
    current_user: OmniUser = Depends(get_current_user)
):
    """
    V1.0 Block 03: Governed Lifecycle Control.
    Suspend or Revoke a connector's execution authority.
    """
    space = space_registry.resolve_space(current_user.id)
    success = connector_registry.update_connector_status(connector_id, status, space.space_id)
    if not success:
        return {"status": "error", "message": "Failed to update status (Check ownership/id)"}
    return {"status": "success", "message": f"Connector {connector_id} is now {status}"}

@router.get("/connectors/history")
async def get_connector_history(
    limit: int = 10,
    current_user: OmniUser = Depends(get_current_user)
):
    """
    V1.0 Block 03: Sovereign Audit History.
    Retrieves the last N records of external tool interactions.
    """
    history = governed_executor.get_execution_history(current_user.id, limit=limit)
    return {
        "status": "success",
        "history": [h.model_dump() for h in history]
    }

@router.get("/connectors/summary")
async def get_dashboard_summary(current_user: OmniUser = Depends(get_current_user)):
    """
    V1.0 Block 05: Dashboard Aggregator.
    Returns a unified view of the Personal Space, Connectors, and History.
    """
    space = space_registry.resolve_space(current_user.id)
    connectors = connector_registry.get_connectors_for_space(space.space_id)
    history = governed_executor.get_execution_history(current_user.id, limit=5)
    
    return {
        "status": "success",
        "space": space.model_dump(),
        "connectors": [c.model_dump() for c in connectors],
        "history": [h.model_dump() for h in history],
        "metrics": {
            "total_connectors": len(connectors),
            "active_connectors": len([c for c in connectors if c.status == "ACTIVE"])
        }
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
