from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

class VectorEntry(BaseModel):
    node_id: str
    embedding: List[float]
    source_type: str # knowledge_node, memory, chip, topic
    text_content: str
    timestamp: datetime = Field(default_factory=datetime.now)

class SemanticSearchResult(BaseModel):
    node_id: str
    source_type: str
    score: float
    text_content: str
