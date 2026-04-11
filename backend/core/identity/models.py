from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict, Any
from enum import Enum
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

class PersonalSpace(BaseModel):
    """
    V1.0 Block 01: Governed Personal Space.
    Maps internal user identity to a persistent data root and isolated context.
    """
    user_id: str
    space_id: str
    space_root: str
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_access: datetime = Field(default_factory=datetime.utcnow)
    identity_ref: str # e.g. "omni-native:user_id"

class OwnedArtifact(BaseModel):
    """
    V1.0 Block 02: Artifact Ownership Metadata.
    Tracks user-generated assets within their Personal Space.
    """
    artifact_id: str
    user_id: str
    space_id: str
    artifact_type: str # NOTE, CODE, MEDIA, RESULT
    filename: str
    relative_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    governance_class: str = "PRIVATE"

class IdentityMapping(BaseModel):
    """
    V1.0 Block 03: External-to-Internal Identity Bridge.
    Maps an external provider account to a sovereign Omni identity.
    """
    mapping_id: str
    provider: str # e.g. "google"
    external_id: str # e.g. Google 'sub'
    internal_id: str # The canonical user_id
    linked_at: datetime = Field(default_factory=datetime.utcnow)
    status: str = "LINKED" # LINKED, REVOKED

class CapabilityClass(str, Enum):
    """V1.0 Block 01: Governed Access Levels."""
    READ_ONLY = "READ_ONLY"
    READ_WRITE = "READ_WRITE"
    EXECUTION_ONLY = "EXECUTION_ONLY"
    ADMIN = "ADMIN"

class ExternalConnector(BaseModel):
    """
    V1.0 Block 01: External App/Tool Metadata.
    Encapsulates a subordinate tool bound to a Personal Space.
    """
    connector_id: str
    owner_space_id: str
    provider_type: str # LOCAL_EXEC | EXTERNAL_API
    capability: CapabilityClass = CapabilityClass.READ_ONLY
    status: str = "ACTIVE" # ACTIVE, SUSPENDED, REVOKED
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    governance_class: str = "GOVERNED"
    config: Dict[str, str] = {} # e.g. {"service_id": "google-drive"}

class ConnectorExecutionResult(BaseModel):
    """
    V1.0 Block 02: Governed Execution Capture.
    Tracks the outcome of a single external connector interaction.
    """
    execution_id: str
    connector_id: str
    user_id: str
    status: str # SUCCESS, FAILURE, DENIED
    message: str
    artifact_ids: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    technical_trace: Dict[str, Any] = {}
