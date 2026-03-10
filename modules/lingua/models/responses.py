from pydantic import BaseModel
from typing import Optional, List

class JobResponse(BaseModel):
    job_id: str
    message: str

class ProgressUpdate(BaseModel):
    stage: str
    percent: float
    status: str

class JobDetailResponse(BaseModel):
    job_id: str
    status: str
    stage: str
    percent: float
    message: str
    result_url: Optional[str] = None
    error: Optional[str] = None
