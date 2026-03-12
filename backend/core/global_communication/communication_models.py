from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid
import time
from backend.core.language_bridge.language_bridge_models import LanguageCode, VoiceStyle

class SessionStatus(str, Enum):
    ACTIVE = "active"
    ENDING = "ending"
    CLOSED = "closed"

class Participant(BaseModel):
    user_id: str
    name: str
    joined_at: float = Field(default_factory=time.time)
    native_language: LanguageCode
    listening_language: LanguageCode
    voice_personality: VoiceStyle = VoiceStyle.FRIENDLY

class CommunicationSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = "OmniWeb Global Call"
    status: SessionStatus = SessionStatus.ACTIVE
    participants: Dict[str, Participant] = {}
    created_at: float = Field(default_factory=time.time)
    metadata: Dict[str, Any] = {}

class VoiceChunk(BaseModel):
    session_id: str
    sender_id: str
    payload: str # Base64 or stream URL reference
    timestamp: float = Field(default_factory=time.time)

class SpatialBubble(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    speaker_id: str
    content: str
    language_flag: str
    position: Dict[str, float] = {"x": 0, "y": 0, "z": 0}
    duration: float = 3.0
