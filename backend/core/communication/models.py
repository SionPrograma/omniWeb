from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime
from enum import Enum
import uuid


class MessageStatus(str, Enum):
    DRAFT = "draft"
    PENDING_CONFIRMATION = "pending_confirmation"
    SENT = "sent"
    DELIVERED = "delivered"
    READ = "read"
    FAILED = "failed"


class CallStatus(str, Enum):
    INITIATING = "initiating"
    RINGING = "ringing"
    ACTIVE = "active"
    ON_HOLD = "on_hold"
    ENDED = "ended"
    MISSED = "missed"
    FAILED = "failed"


class Contact(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    owner_user_id: str
    contact_user_id: Optional[str] = None  # If they are an OmniWeb user
    display_name: str
    nickname: Optional[str] = None
    relationship: Optional[str] = None  # e.g., "brother", "colleague", "friend"
    preferred_language: str = "es"
    email: Optional[str] = None
    phone: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}


class Message(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str
    recipient_contact_id: str
    original_text: str
    original_language: str = "es"
    translated_text: Optional[str] = None
    target_language: Optional[str] = None
    status: MessageStatus = MessageStatus.DRAFT
    channel: str = "omniweb"  # omniweb, email, sms
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}


class CallSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    caller_id: str
    callee_contact_id: str
    status: CallStatus = CallStatus.INITIATING
    start_time: datetime = Field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    duration_seconds: int = 0
    translation_active: bool = False
    metadata: Dict[str, Any] = {}


class ConversationEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    contact_id: str
    direction: str = "outgoing"  # incoming, outgoing
    content_type: str = "message"  # message, call
    content_preview: str = ""
    language: str = "es"
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}
