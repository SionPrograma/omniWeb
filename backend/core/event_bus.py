from typing import Callable, Dict, List, Any
import logging

logger = logging.getLogger(__name__)

class EventBus:
    """
    A simple event bus for communication between modules.
    Follows a basic observer pattern.
    """
    def __init__(self):
        self._subscribers: Dict[str, List[Callable]] = {}

    def subscribe(self, event_type: str, callback: Callable):
        """
        Subscribe to an event type.
        
        Args:
            event_type: The name of the event to listen for.
            callback: The function to call when the event is emitted.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = []
        self._subscribers[event_type].append(callback)
        logger.debug(f"Subscribed to event: {event_type}")

    def emit(self, event_type: str, data: Any = None):
        """
        Emit an event to all subscribers.
        
        Args:
            event_type: The name of the event to emit.
            data: Optional data to pass to the callbacks.
        """
        if event_type in self._subscribers:
            for callback in self._subscribers[event_type]:
                try:
                    callback(data)
                except Exception as e:
                    logger.error(f"Error in event listener for {event_type}: {str(e)}")
        
        logger.debug(f"Emitted event: {event_type}")

# Global instance
event_bus = EventBus()
