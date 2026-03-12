from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
import uuid

class LanguageCode(str, Enum):
    SPANISH = "es"
    ENGLISH = "en"
    ARABIC = "ar"
    FRENCH = "fr"
    GERMAN = "de"
    JAPANESE = "ja"
    CHINESE = "zh"

class VoiceStyle(str, Enum):
    FORMAL = "formal"
    FRIENDLY = "friendly"
    NEUTRAL = "neutral"
    SOFT = "soft"
    ENERGETIC = "energetic"

class Speaker(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    native_language: LanguageCode = LanguageCode.SPANISH

class ConversationSegment(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    speaker_id: str
    original_text: str
    original_language: LanguageCode
    timestamp: float
    duration: float

class TranslatedSegment(BaseModel):
    segment_id: str
    target_language: LanguageCode
    translated_text: str
    pronunciation_guide: Optional[str] = None
    voice_style: VoiceStyle = VoiceStyle.NEUTRAL

class BridgeUserConfig(BaseModel):
    user_id: str
    preferred_listening_language: LanguageCode
    show_subtitles: bool = True
    subtitle_size: str = "medium"
    show_pronunciation: bool = False
    voice_adaptation_style: VoiceStyle = VoiceStyle.FRIENDLY
