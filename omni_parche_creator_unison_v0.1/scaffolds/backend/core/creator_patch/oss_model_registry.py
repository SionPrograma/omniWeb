"""
Additive scaffold for open-source model/tool registry.
Omni should treat external models as governed capabilities, not as authority.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CapabilityRecord:
    capability_id: str
    provider: str
    model_name: str
    capability_type: str
    local: bool = True
    tags: List[str] = field(default_factory=list)
    preferred_for: List[str] = field(default_factory=list)
    notes: str = ""


class OSSModelRegistry:
    def __init__(self) -> None:
        self._records: Dict[str, CapabilityRecord] = {}

    def register(self, record: CapabilityRecord) -> None:
        self._records[record.capability_id] = record

    def get(self, capability_id: str) -> Optional[CapabilityRecord]:
        return self._records.get(capability_id)

    def list_all(self) -> List[CapabilityRecord]:
        return list(self._records.values())

    def find_by_type(self, capability_type: str) -> List[CapabilityRecord]:
        return [r for r in self._records.values() if r.capability_type == capability_type]
