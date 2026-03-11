import logging
import asyncio
import inspect
from typing import Dict, List, Any, Callable, Union

logger = logging.getLogger(__name__)

class EventBus:
    """
    A simple, process-local Event Bus for decoupled communication between OmniWeb chips.
    Supports both synchronous and asynchronous listeners.
    """
    def __init__(self):
        self._listeners: Dict[str, List[Callable]] = {}

    def subscribe(self, event_name: str, handler: Callable):
        """
        Registers a listener for a specific event.
        Prevents duplicate subscriptions for the same handler.
        """
        if event_name not in self._listeners:
            self._listeners[event_name] = []
        
        if handler not in self._listeners[event_name]:
            self._listeners[event_name].append(handler)
            logger.debug(f"Subscribed handler '{handler.__name__}' to event '{event_name}'")

    def unsubscribe(self, event_name: str, handler: Callable):
        """
        Removes a listener for a specific event.
        """
        if event_name in self._listeners and handler in self._listeners[event_name]:
            self._listeners[event_name].remove(handler)
            logger.debug(f"Unsubscribed handler '{handler.__name__}' from event '{event_name}'")

    async def publish(self, event_name: str, payload: Any = None):
        """
        Publishes an event and notifies all registered listeners.
        Supports both sync and async handlers.
        """
        if event_name not in self._listeners:
            logger.debug(f"No listeners for event '{event_name}'")
            return

        logger.info(f"EventBus: Publishing '{event_name}'")
        
        # We'll collect coroutines and handle sync calls immediately
        tasks = []
        for handler in self._listeners[event_name]:
            try:
                if inspect.iscoroutinefunction(handler):
                    tasks.append(self._run_async_handler(handler, event_name, payload))
                else:
                    handler(payload)
            except Exception as e:
                 logger.error(f"EventBus: Error in sync listener '{handler.__name__}' for '{event_name}': {e}")

        if tasks:
            # We use gather to run them concurrently. Exceptions are handled inside _run_async_handler
            await asyncio.gather(*tasks)

    async def _run_async_handler(self, handler: Callable, event_name: str, payload: Any):
        """Internal helper to wrap async handlers with error logging."""
        try:
            await handler(payload)
        except Exception as e:
            logger.error(f"EventBus: Error in async listener '{handler.__name__}' for '{event_name}': {e}")

# Singleton instance for global use
event_bus = EventBus()
