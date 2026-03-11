from enum import Enum
from pydantic import BaseModel
from typing import Optional, List

class AntimodalMode(str, Enum):
    STANDARD = "standard"
    SILENT = "silent"
    COMPACT = "compact"
    BACKGROUND = "background"
    LOW_DISTRACTION = "low_distraction"
    SUMMARY_ONLY = "summary_only"

class AntimodalState(BaseModel):
    current_mode: AntimodalMode = AntimodalMode.STANDARD
    auto_adapt: bool = True
    intensity_level: float = 1.0  # 0.0 to 1.0
    last_interaction_timestamp: float
    focus_target_chip: Optional[str] = None
    suppressed_panels: List[str] = []

class CompactResponse(BaseModel):
    original_length: int
    compact_text: str
    key_points: List[str]
    actions_taken: List[str]
    mode_applied: AntimodalMode
