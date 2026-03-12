from fastapi import APIRouter, Depends, HTTPException, Security
from fastapi.security import OAuth2PasswordRequestForm
from backend.core.auth import (
    get_current_user, 
    get_admin_user, 
    OmniUser, 
    oauth2_scheme,
    verify_password,
    create_session,
    get_password_hash
)
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

router = APIRouter()

@router.post("/token")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authenticates a user and returns a persistent session token.
    """
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute(
                "SELECT id, hashed_password FROM users WHERE username = ?",
                (form_data.username,)
            ).fetchone()
            
            if not row or not verify_password(form_data.password, row["hashed_password"]):
                raise HTTPException(status_code=400, detail="Incorrect username or password")
            
            user_id = row["id"]
            current_hash = row["hashed_password"]

            # Lazy Hash Upgrade: If it's not bcrypt, update it now
            if not (current_hash.startswith("$2b$") or current_hash.startswith("$2a$")):
                new_hash = get_password_hash(form_data.password)
                conn.execute(
                    "UPDATE users SET hashed_password = ? WHERE id = ?",
                    (new_hash, user_id)
                )
                conn.commit()

    # Create persistent session
    token = create_session(user_id)
    return {"access_token": token, "token_type": "bearer"}

@router.get("/me")
async def get_my_profile(current_user: OmniUser = Security(get_current_user)):
    """Returns the profile of the currently authenticated user."""
    return current_user

@router.post("/logout")
async def logout(token: str = Depends(oauth2_scheme)):
    """Inactivates the current session token."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute("DELETE FROM sessions WHERE token = ?", (token,))
            conn.commit()
    return {"status": "success", "message": "Logged out successfully"}
