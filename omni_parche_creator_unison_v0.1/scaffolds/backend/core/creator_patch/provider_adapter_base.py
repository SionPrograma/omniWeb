"""
Unified provider adapter contract.
Each open-source model/tool adapter should conform to this interface.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict


class ProviderAdapterBase(ABC):
    provider_name: str = "unknown"

    @abstractmethod
    def healthcheck(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def run(self, request: Dict[str, Any]) -> Dict[str, Any]:
        raise NotImplementedError
