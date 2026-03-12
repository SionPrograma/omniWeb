from pydantic import BaseModel
from enum import Enum
from typing import List, Optional

class DomainCategory(str, Enum):
    SCIENCE = "science"
    HISTORY = "history"
    PHILOSOPHY = "philosophy"
    RELIGION = "religion"
    POLITICS = "politics"
    TECHNOLOGY = "technology"
    ART = "art"
    HUMAN_DEVELOPMENT = "human development"

class KnowledgeDomain(BaseModel):
    id: str
    name: str
    category: DomainCategory
    description: str
    active_projects_count: int = 0
    total_nodes: int = 0

class DomainSummary(BaseModel):
    domain_id: str
    summary_text: str
    key_concepts: List[str]
    emerging_trends: List[str]
