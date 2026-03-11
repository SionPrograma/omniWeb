from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class KnowledgeNode(BaseModel):
    id: Optional[int] = None
    node_type: str  # topic, concept, project, workflow, chip, learning_domain, skill, session
    name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    importance_score: float = 0.0
    metadata: Dict[str, Any] = Field(default_factory=dict)

class KnowledgeEdge(BaseModel):
    id: Optional[int] = None
    source_node: int
    target_node: int
    relationship: str  # USES, RELATES_TO, PART_OF, LEADS_TO, REQUIRES, EVOLVES_TO, STUDIED_WITH
    weight: float = 1.0
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: Dict[str, Any] = Field(default_factory=dict)

class GraphQuery(BaseModel):
    root_node_id: int
    max_depth: int = 2
    relationship_filter: Optional[List[str]] = None

class GraphQueryResult(BaseModel):
    nodes: List[KnowledgeNode]
    edges: List[KnowledgeEdge]
