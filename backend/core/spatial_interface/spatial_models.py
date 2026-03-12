from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid

class Vector3(BaseModel):
    x: float = 0.0
    y: float = 0.0
    z: float = 0.0

class HologramObject(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    type: str # "agent", "web_page", "knowledge_map", "tool", "simulation"
    position: Vector3 = Field(default_factory=Vector3)
    rotation: Vector3 = Field(default_factory=Vector3)
    scale: Vector3 = Field(default_factory=lambda: Vector3(x=1.0, y=1.0, z=1.0))
    opacity: float = 0.8
    is_anchored: bool = False
    metadata: Dict[str, Any] = {}

class SpatialScene(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    objects: List[HologramObject] = []
    environment_mapped: bool = False
    workspace_360: bool = True
