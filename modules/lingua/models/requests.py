from pydantic import BaseModel, HttpUrl
from typing import Optional

class TranslationRequest(BaseModel):
    url: Optional[str] = None
    target_lang: str = "es"
    voice_clone: bool = False

class JobStatusResponse(BaseModel):
    job_id: str
    status: str
    progress: float
    message: str
    result_url: Optional[str] = None
