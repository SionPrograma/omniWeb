from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List, Dict, Any
from .environment_detector import EnvironmentType

class RuntimeState(BaseModel):
    boot_time: datetime = Field(default_factory=datetime.now)
    environment: EnvironmentType = EnvironmentType.DESKTOP
    hostname: str = "unknown"
    profile_name: str = "default"
    is_portable: bool = False
    system_health: str = "ok"
    active_services: List[str] = []
    metadata: Dict[str, Any] = {}

    def get_uptime(self) -> float:
        return (datetime.now() - self.boot_time).total_seconds()
