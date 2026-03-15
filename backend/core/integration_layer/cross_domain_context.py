from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)

class CrossDomainContext:
    """
    Maintains shared context between domains during complex orchestrations.
    Allows domains to pass localized memory without tight coupling.
    """
    def __init__(self):
        self._shared_memory: Dict[str, Any] = {}

    def set_context(self, key: str, value: Any, domain: str):
        self._shared_memory[key] = {
            "value": value,
            "owner": domain
        }
        logger.debug(f"CrossDomainContext: {domain} set '{key}'")

    def get_context(self, key: str) -> Optional[Any]:
        entry = self._shared_memory.get(key)
        return entry["value"] if entry else None

    def clear(self):
        self._shared_memory.clear()

cross_domain_context = CrossDomainContext()
