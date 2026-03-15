import os
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum

class AuditStatus(str, Enum):
    PASS = "PASS"
    WARNING = "WARNING"
    ERROR = "ERROR"

class AuditSector(str, Enum):
    FRONTEND = "FRONTEND"
    BACKEND = "BACKEND"
    CHIPS = "CHIPS"
    PWA = "PWA"
    PERFORMANCE = "PERFORMANCE"

class AuditIssue(BaseModel):
    sector: AuditSector
    level: AuditStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    fingerprint: Optional[str] = None # For matching with fixable signatures

class SystemAuditReport(BaseModel):
    timestamp: datetime = Field(default_factory=datetime.now)
    overall_status: AuditStatus
    summary: str
    issues: List[AuditIssue] = []
    metrics: Dict[str, Any] = {}

class FixAction(BaseModel):
    type: str # 'file_patch', 'module_reload', 'cleanup', 'config_update'
    target: str # path or module slug
    description: str
    patch_data: Optional[Dict[str, Any]] = None

class AutoFixProposal(BaseModel):
    id: str = Field(default_factory=lambda: f"fix-{datetime.now().strftime('%Y%m%d%H%M%S')}-{os.urandom(2).hex()}")
    issue_message: str
    analysis: str
    actions: List[FixAction]
    status: str = "pending" # pending, approved, applied, failed, successful
    timestamp: datetime = Field(default_factory=datetime.now)
