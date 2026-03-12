from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid

class Idea(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    raw_thought: str
    timestamp: datetime = Field(default_factory=datetime.now)
    user_context: Dict[str, Any] = {}
    semantic_vector: Optional[List[float]] = None
    topics: List[str] = []
    sentiment: float = 0.0 # -1.0 to 1.0
    linked_nodes: List[str] = [] # IDs of Knowledge Graph nodes
    linked_memories: List[str] = [] # IDs of Long Term Memories
    is_processed: bool = False
    suggested_actions: List[str] = []

class IdeaCluster(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    idea_ids: List[str] = []
    summary: str
    emerging_project: bool = False
    last_updated: datetime = Field(default_factory=datetime.now)
