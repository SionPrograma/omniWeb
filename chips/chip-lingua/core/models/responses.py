from pydantic import BaseModel
from typing import Optional, List

class JobResponse(BaseModel):
    job_id: str
    message: str

class ProgressUpdate(BaseModel):
    stage: str
    percent: float
    status: str
    message: Optional[str] = None # Added for V1.6 visibility

class JobDetailResponse(BaseModel):
    job_id: str
    status: str
    stage: str
    percent: float
    message: str
    progress: List[ProgressUpdate] = [] # Added for V1.6 visibility
    result_url: Optional[str] = None
    error: Optional[str] = None
    is_purged: bool = False # Added for V1.9 Governance Truth

class PurgeAuditItem(BaseModel):
    job_id: str
    original_status: str
    reason: str
    purged_at: str
    media_cleared: bool

class GovernanceAuditResponse(BaseModel):
    purges: List[PurgeAuditItem]

class JobArchiveExport(BaseModel):
    metadata: JobDetailResponse
    retained_outputs: List[str] # Paths to files still on disk

class TextTranslateResponse(BaseModel):
    translation: str
    transliteration: str
    pronunciation: str
