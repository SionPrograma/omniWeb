from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class MusicIdeaBase(BaseModel):
    title: str
    content: str
    scale_context: Optional[str] = None

class MusicIdeaCreate(MusicIdeaBase):
    pass

class MusicIdea(MusicIdeaBase):
    id: int
    created_at: str

    class Config:
        from_attributes = True

class MusicIdeaResponse(BaseModel):
    status: str
    data: List[MusicIdea]
