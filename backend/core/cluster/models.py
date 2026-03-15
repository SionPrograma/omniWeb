from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from enum import Enum
from datetime import datetime

class NodeRole(str, Enum):
    PRIMARY = "primary"
    WORKER = "worker"
    STORAGE = "storage"
    EDGE = "edge"

class NodeStatus(str, Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    DRAINING = "draining"
    MAINTENANCE = "maintenance"

class HeartbeatPayload(BaseModel):
    node_id: str
    cpu_usage: float
    memory_usage: float
    active_chips: int
    latency: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    signature: Optional[str] = None # For signed communication (Phase 24)

class ClusterNode(BaseModel):
    node_id: str
    node_role: NodeRole
    node_region: str
    node_status: NodeStatus
    node_url: str
    uptime: int
    last_heartbeat: datetime
    cpu_usage: float
    memory_usage: float
    active_chips: int
    latency: float
    connected_services: List[str]
    metadata: Dict[str, Any] = {}

class ClusterState(BaseModel):
    active_nodes: int
    total_nodes: int
    nodes: List[ClusterNode]
    cluster_load: float # Avg CPU across workers
    storage_nodes: int
    edge_nodes: int
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class NodeOperation(BaseModel):
    operation: str # drain, restart, disable, enable
    target_node_id: str

# PHASE 25 - Workload Distribution Models
class TaskStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"

class ChipTask(BaseModel):
    task_id: str
    chip_slug: str
    worker_node_id: Optional[str] = None
    requesting_user_id: str
    status: TaskStatus = TaskStatus.PENDING
    execution_context: Dict[str, Any] = {}
    result_payload: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

class WorkloadState(BaseModel):
    active_tasks: int
    queued_tasks: int
    completed_tasks: int
    failed_tasks: int
    worker_distribution: Dict[str, int] # node_id -> active_tasks
    avg_task_latency: float # ms
    tasks: List[ChipTask]

# PHASE 29 - Distributed Storage Grid Models
class StorageBlock(BaseModel):
    block_id: str
    data_type: str
    size_bytes: int
    content_hash: str
    metadata: Dict[str, Any] = {}
    created_at: datetime = Field(default_factory=datetime.utcnow)

class StorageFragment(BaseModel):
    fragment_id: str
    block_id: str
    node_id: str
    status: str
    fragment_index: int
    replicated_to: List[str] = []

class StorageGridState(BaseModel):
    total_capacity: int # Bytes
    used_capacity: int # Bytes
    available_nodes: int
    replication_factor: int
    healthy_blocks: int
    corrupt_blocks: int
    blocks: List[StorageBlock] = []
