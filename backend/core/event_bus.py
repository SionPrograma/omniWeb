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
        # Stores list of dicts: {"handler": Callable, "chip_slug": str}
        self._listeners: Dict[str, List[Dict[str, Any]]] = {}

    def subscribe(self, event_name: str, handler: Callable):
        """
        Registers a listener for a specific event.
        Prevents duplicate subscriptions for the same handler.
        """
        from backend.core.permissions import enforce_permission, get_current_chip
        try:
            enforce_permission("event_subscribe")
        except Exception as e:
            logger.error(f"EventBus: Subscribe denied for '{event_name}': {e}")
            raise

        if event_name not in self._listeners:
            self._listeners[event_name] = []
        
        # Check against existing handlers
        if not any(l["handler"] == handler for l in self._listeners[event_name]):
            self._listeners[event_name].append({
                "handler": handler,
                "chip_slug": get_current_chip()
            })
            logger.debug(f"Subscribed handler '{handler.__name__}' to event '{event_name}' context '{get_current_chip()}'")

    def unsubscribe(self, event_name: str, handler: Callable):
        """
        Removes a listener for a specific event.
        """
        if event_name in self._listeners:
            self._listeners[event_name] = [l for l in self._listeners[event_name] if l["handler"] != handler]
            logger.debug(f"Unsubscribed handler '{handler.__name__}' from event '{event_name}'")

    async def publish(self, event_name: str, payload: Any = None):
        """
        Publishes an event and notifies all registered listeners.
        Supports both sync and async handlers.
        """
        from backend.core.permissions import enforce_permission
        try:
            enforce_permission("event_publish")
        except Exception as e:
            logger.error(f"EventBus: Publish denied for '{event_name}': {e}")
            raise

        # Collect tasks (persistence + async handlers)
        tasks = [self._persist_event(event_name, payload)]

        if event_name not in self._listeners:
            logger.debug(f"No listeners for event '{event_name}'. Event persisted.")
            await asyncio.gather(*tasks)
            return

        logger.info(f"EventBus: Publishing '{event_name}'")
        
        from backend.core.permissions import set_chip_context

        for listener in self._listeners[event_name]:
            handler = listener["handler"]
            chip_slug = listener["chip_slug"]
            
            try:
                if inspect.iscoroutinefunction(handler):
                    tasks.append(self._run_async_handler(handler, event_name, payload, chip_slug))
                else:
                    if chip_slug:
                        with set_chip_context(chip_slug):
                            handler(payload)
                    else:
                        handler(payload)
            except Exception as e:
                 logger.error(f"EventBus: Error in sync listener '{handler.__name__}' for '{event_name}': {e}")

        if tasks:
            # We use gather to run them concurrently. Exceptions are handled inside _run_async_handler
            await asyncio.gather(*tasks)

        # Distributed Routing (Trigger outgoing distribution)
        # Only if not already coming from another node
        if not (isinstance(payload, dict) and payload.get("_distributed_ignore")):
            try:
                from backend.core.distributed_bus.distributed_event_router import distributed_event_router
                from backend.core.permissions import get_current_chip
                asyncio.create_task(distributed_event_router.route_outgoing(
                    event_name, payload, chip_context=get_current_chip()
                ))
            except Exception as e:
                logger.warning(f"EventBus: Distributed routing failed for '{event_name}': {e}")

    async def _run_async_handler(self, handler: Callable, event_name: str, payload: Any, chip_slug: Optional[str]):
        """Internal helper to wrap async handlers with error logging and context propagation."""
        from backend.core.permissions import set_chip_context
        try:
            if chip_slug:
                with set_chip_context(chip_slug):
                    await handler(payload)
            else:
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

            # 4. Usage Analytics Integration (Phase F)
            try:
                from backend.core.usage.usage_tracker import usage_tracker
                usage_tracker.log_event(
                    event_type=event_name,
                    chip_slug=source,
                    metadata=payload if isinstance(payload, dict) else {"payload": payload_json}
                )
            except Exception as usage_err:
                logger.warning(f"EventBus: Usage tracking failed for '{event_name}': {usage_err}")
                
        except Exception as e:
            logger.error(f"EventBus: Critical persistence failure for '{event_name}': {e}")

# Singleton instance for global use
event_bus = EventBus()
