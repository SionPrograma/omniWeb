from pydantic import BaseModel, EmailStr
from typing import Optional, List
from datetime import datetime

class UserIdentity(BaseModel):
    user_id: str
    provider: str
    display_name: str
    email: Optional[str] = None
    avatar: Optional[str] = None

class OAuthToken(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None

class SessionInfo(BaseModel):
    session_id: str
    user_id: str
    token: str
    expires_at: datetime
    identity: UserIdentity
