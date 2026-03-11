import logging
import asyncio
import inspect
import json
from typing import Dict, List, Any, Callable, Optional, Union
from backend.core.database import db_manager

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
        # Collect tasks (persistence + async handlers)
        tasks = [self._persist_event(event_name, payload)]

        if event_name not in self._listeners:
            logger.debug(f"No listeners for event '{event_name}'. Event persisted.")
            await asyncio.gather(*tasks)
            return

        logger.info(f"EventBus: Publishing '{event_name}'")
        
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

    async def _persist_event(self, event_name: str, payload: Any):
        """
        Saves interest events to SQLite for audit.
        Ensures that failures in persistence do not affect the main event flow.
        """
        try:
            # 1. Safe JSON Serialization
            try:
                payload_json = json.dumps(payload) if payload is not None else None
            except (TypeError, ValueError) as json_err:
                logger.warning(f"EventBus: Could not serialize payload for '{event_name}': {json_err}")
                payload_json = f"<Non-serializable: {type(payload).__name__}>"

            # 2. Safe Source Extraction
            source = None
            if isinstance(payload, dict):
                source = payload.get("source_chip")

            # 3. Database Insertion
            with db_manager.get_connection() as conn:
                conn.execute(
                    "INSERT INTO system_events (event_name, payload, source_chip) VALUES (?, ?, ?)",
                    (event_name, payload_json, source)
                )
                conn.commit()
                
        except Exception as e:
            logger.error(f"EventBus: Critical persistence failure for '{event_name}': {e}")

# Singleton instance for global use
event_bus = EventBus()
