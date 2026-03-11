import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class InterfaceAdapter:
    """
    Base class for multimodal interface adapters.
    """
    def process_input(self, input_data: Any) -> str:
        raise NotImplementedError("Subclasses must implement process_input")

    def format_output(self, response: Dict[str, Any]) -> Any:
        raise NotImplementedError("Subclasses must implement format_output")
