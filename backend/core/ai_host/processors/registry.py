from typing import Dict, Type
from .base import CommandProcessor

class ProcessorRegistry:
    """
    Registry for dynamic discovery and management of command processors.
    Supports Phase T: Universal Knowledge Command System.
    """
    def __init__(self):
        self._processors: Dict[str, CommandProcessor] = {}

    def register(self, intent: str, processor: CommandProcessor):
        self._processors[intent] = processor

    def get_processor(self, intent: str) -> CommandProcessor:
        return self._processors.get(intent)

processor_registry = ProcessorRegistry()
