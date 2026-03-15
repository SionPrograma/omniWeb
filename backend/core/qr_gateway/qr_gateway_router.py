from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse, JSONResponse
from typing import List, Optional
from backend.core.auth import get_admin_user
from .qr_token_manager import qr_token_manager
from .qr_session_resolver import qr_session_resolver
from .qr_visual_generator import qr_visual_generator
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/join")
async def qr_join(token: str):
    """
    Endpoint for QR scanning.
    Validates token, creates session, and redirects to shell.
    """
    session_token = await qr_session_resolver.resolve_session(token)
    if not session_token:
        # Redirect to unauthorized error page or home with error
        return RedirectResponse(url="/?error=invalid_qr_token")

    # Redirect to shell with session injected (in a REAL scenario, we set a cookie)
    response = RedirectResponse(url="/shell/")
    response.set_cookie(key="omniweb_session", value=session_token, httponly=True)
    return response

@router.post("/generate")
async def generate_token_endpoint(
    role: str,
    expires_in: int = 3600,
    single_use: bool = False,
    admin_user: dict = Depends(get_admin_user)
):
    """Admin: Generates a new access token and returns the QR link mapping."""
    token = qr_token_manager.generate_token(role, expires_in, single_use)
    # Construct absolute link (placeholder for production domain)
    base_url = "http://localhost:8000/api/v1/qr"
    join_url = f"{base_url}/join?token={token}"
    
    return {
        "token": token,
        "join_url": join_url,
        "role": role,
        "expires_in": expires_in
    }

@router.get("/tokens")
async def list_active_tokens(admin_user: dict = Depends(get_admin_user)):
    """Admin: Lists all currently valid QR tokens."""
    return qr_token_manager.get_all_active_tokens()

@router.post("/refresh-visuals")
async def refresh_qr_visuals(admin_user: dict = Depends(get_admin_user)):
    """Admin: Regenerates the standard set of 5 branded QRs."""
    roles = ["creator", "admin", "admin_candidate", "beta_tester", "public"]
    results = []
    
    for role in roles:
        # Create persistent reusable tokens for these master QRs (or long-lived ones)
        token = qr_token_manager.generate_token(role, expires_in=31536000, single_use=False) 
        join_url = f"http://localhost:8000/api/v1/qr/join?token={token}"
        path = qr_visual_generator.generate_branded_qr(f"omniweb_qr_{role}", join_url)
        results.append({"role": role, "path": path})
        
    return {"status": "success", "generated": results}
