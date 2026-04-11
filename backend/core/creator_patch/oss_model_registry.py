"""
OSS Model Registry — OMNI_PATCH Phase D.
Registers external/open-source models as subordinate governed capabilities.
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

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
    """
    Governed registry for non-Omni models and tools.
    """

    def __init__(self) -> None:
        self._records: Dict[str, CapabilityRecord] = {}
        self._seed_default_capabilities()

    def _seed_default_capabilities(self):
        """Seed the registry with common OSS capabilities."""
        defaults = [
            CapabilityRecord(
                capability_id="oss_llama3_local",
                provider="ollama",
                model_name="llama3:latest",
                capability_type="reasoning",
                local=True,
                tags=["oss", "fast", "local"],
                preferred_for=["summarization", "quick_analysis"]
            ),
            CapabilityRecord(
                capability_id="oss_coder_shell",
                provider="local_exec",
                model_name="deepseek-coder",
                capability_type="code",
                local=True,
                tags=["oss", "logic"],
                preferred_for=["refactoring", "unit_tests"]
            ),
            CapabilityRecord(
                capability_id="oss_sd_image",
                provider="diffusers",
                model_name="stable-diffusion-v1-5",
                capability_type="multimodal",
                local=True,
                tags=["oss", "visual"],
                preferred_for=["mockups", "diagrams"]
            )
        ]
        for record in defaults:
            self.register(record)
        logger.info(f"[OSS_REGISTRY] Seeded {len(defaults)} capabilities.")

    def register(self, record: CapabilityRecord) -> None:
        logger.info(f"[OSS_REGISTRY] Registering capability: {record.capability_id}")
        self._records[record.capability_id] = record

    def get(self, capability_id: str) -> Optional[CapabilityRecord]:
        return self._records.get(capability_id)

    def list_all(self) -> List[CapabilityRecord]:
        return list(self._records.values())

    def find_by_type(self, capability_type: str) -> List[CapabilityRecord]:
        return [r for r in self._records.values() if r.capability_type == capability_type]

oss_model_registry = OSSModelRegistry()
