from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional
from backend.core.config import settings

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False)

class OmniUser(BaseModel):
    id: str
    username: str
    role: str

def get_current_user(token: Optional[str] = Security(oauth2_scheme)) -> OmniUser:
    """
    Validates the bearer token.
    For local OS architecture, if token matches ADMIN_TOKEN, authenticates as admin.
    """
    if not token or token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return OmniUser(id="1", username="admin", role="admin")

def require_role(required_role: str):
    """
    Dependency that ensures the authenticated user has the necessary role.
    """
    def role_checker(current_user: OmniUser = Security(get_current_user)):
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role: {required_role}"
            )
        return current_user
    return role_checker

def get_admin_user(current_user: OmniUser = Security(require_role("admin"))):
    """Convenience dependency for admin operations."""
    return current_user
