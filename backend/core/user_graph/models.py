from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

class GraphNode(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    entry_id: Optional[str] = None
    node_type: str # idea, task, note, chip_event
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = {}

class GraphEdge(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    source_node: str
    target_node: str
    relation_type: str # related_to, derived_from, depends_on, mentions_chip
    confidence_score: float = 1.0
    metadata: Dict[str, Any] = {}

class GraphQueryResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]
