"""
Provider Adapter Base — OMNI_PATCH Phase D.
Abstract base for external model/tool providers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict
import logging

logger = logging.getLogger(__name__)

class ProviderAdapterBase(ABC):
    provider_name: str = "unknown"

    @abstractmethod
    async def healthcheck(self) -> bool:
        """Verify if the provider service is reachable."""
        raise NotImplementedError

    @abstractmethod
    async def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a request against the provider."""
        raise NotImplementedError

    def log_action(self, action: str, details: Any):
        logger.info(f"[PROVIDER_ADAPTER:{self.provider_name}] {action}: {details}")
