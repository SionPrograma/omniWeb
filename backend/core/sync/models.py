from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum
from datetime import datetime

class SyncAction(str, Enum):
    UPLOAD = "UPLOAD"
    DOWNLOAD = "DOWNLOAD"
    CONFLICT_RESOLVED = "CONFLICT_RESOLVED"

class SyncStatus(str, Enum):
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    WARNING = "WARNING"

class DeviceInfo(BaseModel):
    device_id: str
    user_id: str
    device_name: str
    last_sync: Optional[datetime] = None
    trust_level: int = 1
    metadata: Dict[str, Any] = {}

class SyncPackage(BaseModel):
    device_id: str
    user_id: str
    timestamp: float
    logbook_entries: List[Dict[str, Any]] = []
    graph_nodes: List[Dict[str, Any]] = []
    graph_edges: List[Dict[str, Any]] = []
    tombstones: List[Dict[str, Any]] = []
    workspace_files: List[Dict[str, Any]] = [] # {path, content_b64, hash, modified_at}
    settings: Dict[str, Any] = {}
