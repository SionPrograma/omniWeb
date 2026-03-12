from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum

class InteractionMode(str, Enum):
    DESKTOP = "desktop"
    SPATIAL = "spatial"
    VOICE = "voice"
    DISTRIBUTED = "distributed"

class WorkspaceState(BaseModel):
    id: str = "main_workspace"
    active_tools: List[str] = [] # List of chip/window IDs
    active_agents: List[str] = []
    current_mode: InteractionMode = InteractionMode.DESKTOP
    focus_target: Optional[str] = None # ID of the focused element
    layout_profile: str = "default"

class KnowledgeOSConfig(BaseModel):
    kernel_version: str = "2.0.0"
    is_multi_ai_enabled: bool = True
    is_spatial_ready: bool = True
    active_llm_providers: List[str] = ["openai", "gemini", "local"]
