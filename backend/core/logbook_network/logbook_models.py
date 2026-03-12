from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from datetime import datetime
from enum import Enum

class EntryType(str, Enum):
    IDEA = "idea"
    KNOWLEDGE = "knowledge"
    PROJECT = "project"
    SKILL = "skill"
    INTEREST = "interest"
    CONVERSATION = "conversation"
    LEARNING_PATH = "learning_path"

class LogbookEntry(BaseModel):
    id: str
    type: EntryType
    content: Any
    tags: List[str] = []
    timestamp: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = {}

class ConnectionType(str, Enum):
    CONVERSATION = "conversation"
    COLLABORATION = "collaboration"
    LEARNING_PARTNERSHIP = "learning_partnership"
    RESEARCH_GROUP = "research_group"

class LogbookConnection(BaseModel):
    target_logbook_id: str
    type: ConnectionType
    since: datetime = Field(default_factory=datetime.now)
    status: str = "active"

class Logbook(BaseModel):
    id: str
    owner_id: str
    owner_name: str
    entries: List[LogbookEntry] = []
    knowledge_topics: List[str] = []
    active_projects: List[str] = []
    skills: Dict[str, float] = {}  # skill_name: level (0.0 to 1.0)
    connections: List[LogbookConnection] = []
    last_updated: datetime = Field(default_factory=datetime.now)
    privacy_level: str = "private" # private, semi-private (affinity only), public

class AffinitySignal(BaseModel):
    source_logbook_id: str
    target_logbook_id: str
    score: float
    matching_topics: List[str]
    matching_projects: List[str]
    suggested_connection_type: ConnectionType
