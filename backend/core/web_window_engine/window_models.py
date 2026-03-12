from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uuid

class WebWindow(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    title: str
    width: int = 800
    height: int = 600
    x: int = 50
    y: int = 50
    opacity: float = 0.95
    is_pinned: bool = False
    is_minimized: bool = False

class LayoutConfig(BaseModel):
    theme: str = "dark"
    brightness: float = 1.0
    transparency: float = 0.8
    interactivity_mode: str = "standard" # "standard", "immersive"
