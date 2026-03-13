import os
import uuid
import logging
import shutil
from datetime import datetime, timedelta
import secrets
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .models import UserIdentity, SessionInfo

logger = logging.getLogger(__name__)

class IdentitySessionManager:
    def __init__(self):
        self.workspace_root = "user_workspace"
        os.makedirs(self.workspace_root, exist_ok=True)

    def get_or_create_user(self, identity: UserIdentity) -> str:
        """
        Syncs OAuth identity with local DB.
        Returns the internal user_id.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Find by provider link
                row = conn.execute(
                    "SELECT id FROM users WHERE provider = ? AND provider_id = ?",
                    (identity.provider, identity.user_id)
                ).fetchone()
                
                if row:
                    internal_id = row["id"]
                    # Update profile info
                    conn.execute(
                        "UPDATE users SET display_name = ?, avatar = ?, email = ?, last_login = ? WHERE id = ?",
                        (identity.display_name, identity.avatar, identity.email, datetime.utcnow().isoformat(), internal_id)
                    )
                else:
                    # check if email matches existing local user? 
                    # For simplicity, we create a new user per provider-id combo
                    internal_id = str(uuid.uuid4())
                    username = f"{identity.provider}_{identity.user_id}"
                    
                    conn.execute(
                        """
                        INSERT INTO users (id, username, hashed_password, role, provider, provider_id, display_name, email, avatar, last_login)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (internal_id, username, "oauth-managed", "user", 
                         identity.provider, identity.user_id, identity.display_name, 
                         identity.email, identity.avatar, datetime.utcnow().isoformat())
                    )
                    logger.info(f"Created new user via {identity.provider}: {internal_id}")
                    
                    # 🚀 WORKSPACE CREATION (Phase 15)
                    self._initialize_workspace(internal_id)
                
                conn.commit()
                return internal_id

    def _initialize_workspace(self, user_id: str):
        path = os.path.join(self.workspace_root, user_id)
        if not os.path.exists(path):
            os.makedirs(path)
            # Add basic structure
            os.makedirs(os.path.join(path, "projects"))
            os.makedirs(os.path.join(path, "settings"))
            with open(os.path.join(path, "README.md"), "w", encoding="utf-8") as f:
                f.write(f"# Workspace for User {user_id}\nWelcome to your OmniWeb home.")
            logger.info(f"Initialized workspace for user: {user_id}")

    def create_session(self, user_id: str, identity: UserIdentity) -> SessionInfo:
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
                
        return SessionInfo(
            session_id=session_id,
            user_id=user_id,
            token=token,
            expires_at=expires_at,
            identity=identity
        )

identity_session_manager = IdentitySessionManager()
