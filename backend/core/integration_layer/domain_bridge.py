import logging
from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

class DomainBridge(ABC):
    """
    Base class for connecting major OmniWeb domains.
    Provides a standardized interface for cross-domain orchestration.
    """
    def __init__(self, bridge_id: str, domains: List[str]):
        self.bridge_id = bridge_id
        self.domains = domains
        self.active = True

    @abstractmethod
    async def initialize(self):
        """Initializes the bridge and registers listeners."""
        pass

    @abstractmethod
    async def shutdown(self):
        """Cleans up listeners."""
        pass

    def get_status(self) -> Dict[str, Any]:
        return {
            "bridge_id": self.bridge_id,
            "domains": self.domains,
            "active": self.active
        }
