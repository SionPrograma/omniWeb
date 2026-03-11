import logging
from fastapi import Depends, HTTPException, status, Security
from fastapi.security import OAuth2PasswordBearer
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime, timedelta
import uuid
import secrets
from backend.core.config import settings
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False)

class OmniUser(BaseModel):
    id: str
    username: str
    role: str
    is_active: bool = True

class Session(BaseModel):
    id: str
    user_id: str
    token: str
    expires_at: datetime

def get_user_by_username(username: str) -> Optional[OmniUser]:
    """Retrieves a user from the database by username."""
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute(
                "SELECT id, username, role, is_active FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            if row:
                return OmniUser(
                    id=row["id"],
                    username=row["username"],
                    role=row["role"],
                    is_active=bool(row["is_active"])
                )
    return None

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verifies a password against its hash. 
    Supports bcrypt and provides a safe fallback for dev-mock hashes.
    """
    # 1. Standard Bcrypt verification
    if hashed_password.startswith("$2b$") or hashed_password.startswith("$2a$"):
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception:
            return False

    # 2. Legacy fallback for the simple seed 'admin' -> 'admin-hash'
    if hashed_password == "admin-hash" and plain_password == "admin":
        logger.warning("Using legacy 'admin-hash'. Please update your password.")
        return True
        
    # 3. Fallback for the development mock 'hash_' prefix
    if hashed_password.startswith("hash_"):
        return hashed_password == f"hash_{plain_password}"
        
    return hashed_password == plain_password

def get_password_hash(password: str) -> str:
    """
    Generates a secure bcrypt hash for a plain text password.
    """
    return pwd_context.hash(password)

def create_session(user_id: str) -> str:
    """Creates a new session in the database and returns the token."""
    token = secrets.token_urlsafe(32)
    session_id = str(uuid.uuid4())
    expires_at = datetime.utcnow() + timedelta(days=7)
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            conn.execute(
                "INSERT INTO sessions (id, user_id, token, expires_at) VALUES (?, ?, ?, ?)",
                (session_id, user_id, token, expires_at.isoformat())
            )
            conn.commit()
    return token

def get_current_user(token: Optional[str] = Security(oauth2_scheme)) -> OmniUser:
    """
    Validates the bearer token against the database sessions.
    Also supports the legacy ADMIN_TOKEN for core operations/CLI.
    """
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # 1. Check legacy/static admin token
    if token == settings.ADMIN_TOKEN:
        return OmniUser(id="1", username="admin", role="admin")

    # 2. Check dynamic sessions
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            row = conn.execute(
                """
                SELECT u.id, u.username, u.role, u.is_active 
                FROM users u 
                JOIN sessions s ON u.id = s.user_id 
                WHERE s.token = ? AND s.expires_at > ?
                """,
                (token, datetime.utcnow().isoformat())
            ).fetchone()
            
            if row:
                return OmniUser(
                    id=row["id"],
                    username=row["username"],
                    role=row["role"],
                    is_active=bool(row["is_active"])
                )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )

def require_role(required_role: str):
    """
    Dependency that ensures the authenticated user has the necessary role.
    """
    def role_checker(current_user: OmniUser = Security(get_current_user)):
        if current_user.role != required_role and current_user.role != "admin":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires role: {required_role}"
            )
        return current_user
    return role_checker

def get_admin_user(current_user: OmniUser = Security(require_role("admin"))):
    """Convenience dependency for admin operations."""
    return current_user
