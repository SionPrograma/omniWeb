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
from backend.core.governance.mode_registry import OmniMode, ModePermission, mode_registry
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token", auto_error=False)

class OmniUser(BaseModel):
    id: str
    username: str
    role: str
    mode: OmniMode
    is_active: bool = True

    @classmethod
    def resolve_mode(cls, username: str, role: str, stored_mode: str = None) -> OmniMode:
        """OMNIWEB V1.0: Maps legacy roles or stored values to formal modes."""
        # 1. Admin/Root override
        if username == "admin": return OmniMode.CREATOR
        
        # 2. Prefer stored mode if valid
        if stored_mode:
            try:
                return OmniMode(stored_mode)
            except ValueError:
                pass
        
        # 3. Fallback to role mapping
        if role == "creator": return OmniMode.CREATOR
        if role == "admin": return OmniMode.ADMIN
        if role == "tester": return OmniMode.TESTER
        return OmniMode.PUBLIC

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
                "SELECT id, username, role, mode, is_active FROM users WHERE username = ?",
                (username,)
            ).fetchone()
            if row:
                return OmniUser(
                    id=row["id"],
                    username=row["username"],
                    role=row["role"],
                    mode=OmniUser.resolve_mode(row["username"], row["role"], row["mode"]),
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

    user = None
    # 1. Check legacy/static admin token
    if token == settings.ADMIN_TOKEN:
        user = OmniUser(id="1", username="admin", role="admin", mode=OmniMode.CREATOR)

    # 2. Check dynamic sessions
    if not user:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                row = conn.execute(
                    """
                    SELECT u.id, u.username, u.role, u.mode, u.is_active 
                    FROM users u 
                    JOIN sessions s ON u.id = s.user_id 
                    WHERE s.token = ? AND s.expires_at > ?
                    """,
                    (token, datetime.utcnow().isoformat())
                ).fetchone()
                
                if row:
                    user = OmniUser(
                        id=row["id"],
                        username=row["username"],
                        role=row["role"],
                        mode=OmniUser.resolve_mode(row["username"], row["role"], row["mode"]),
                        is_active=bool(row["is_active"])
                    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # SECURE CONTEXT PROPAGATION
    # Inject user_id into the global context for permission enforcement
    from backend.core.permissions import _current_chip_ctx
    try:
        ctx = _current_chip_ctx.get().copy()
        ctx["user_id"] = user.id
        _current_chip_ctx.set(ctx)
    except Exception:
        pass # Failsafe for cases where context is not initialized

    return user

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

def get_admin_user(current_user: OmniUser = Security(get_current_user)):
    """Convenience dependency for admin operations (V1.0 Mode aware)."""
    if not mode_registry.has_permission(current_user.mode, ModePermission.SYSTEM_MAINTENANCE):
        raise HTTPException(status_code=403, detail="Admin level privileges required.")
    return current_user

def require_permission(perm: ModePermission):
    """
    V1.0 Mode-based permission guard.
    """
    def permission_checker(current_user: OmniUser = Security(get_current_user)):
        if not mode_registry.has_permission(current_user.mode, perm):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires permission: {perm.value} in {current_user.mode.value} mode."
            )
        return current_user
    return permission_checker
