import secrets
import time
from typing import Optional, Dict
from pydantic import BaseModel

class QRToken(BaseModel):
    token: str
    role: str
    created_at: float
    expires_at: Optional[float] = None
    single_use: bool = False
    used: bool = False

class QRTokenManager:
    """
    Manages secure tokens for QR-based access.
    Supports role encoding, expiration, and usage tracking.
    """
    def __init__(self):
        # In a production environment, this would use Redis or a Database
        self._tokens: Dict[str, QRToken] = {}

    def generate_token(self, role: str, expires_in: Optional[int] = 3600, single_use: bool = False) -> str:
        """
        Generates a secure token mapped to a specific role.
        """
        token_str = secrets.token_urlsafe(24)
        expires_at = time.time() + expires_in if expires_in else None
        
        qr_token = QRToken(
            token=token_str,
            role=role,
            created_at=time.time(),
            expires_at=expires_at,
            single_use=single_use
        )
        
        self._tokens[token_str] = qr_token
        return token_str

    def validate_token(self, token_str: str) -> Optional[QRToken]:
        """
        Verifies token existence, expiration, and usage status.
        """
        token = self._tokens.get(token_str)
        if not token:
            return None
        
        # Check expiration
        if token.expires_at and time.time() > token.expires_at:
            del self._tokens[token_str]
            return None
            
        # Check usage
        if token.single_use and token.used:
            return None
            
        return token

    def mark_used(self, token_str: str):
        """Marks a token as consumed."""
        if token_str in self._tokens:
            if self._tokens[token_str].single_use:
                del self._tokens[token_str]
            else:
                self._tokens[token_str].used = True

    def get_all_active_tokens(self) -> Dict[str, QRToken]:
        """Returns all valid non-expired tokens."""
        now = time.time()
        return {t: v for t, v in self._tokens.items() if not v.expires_at or v.expires_at > now}

qr_token_manager = QRTokenManager()
