import json
import logging
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from datetime import datetime

logger = logging.getLogger(__name__)

class DistributedEvent(BaseModel):
    event_id: str
    event_name: str
    origin_node: str
    timestamp: float = Field(default_factory=lambda: datetime.now().timestamp())
    chip_context: Optional[str] = None
    payload: Any
    permission_metadata: Dict[str, Any] = {}

class EventSerializer:
    """
    Handles serialization and validation of events for cross-node transport.
    """
    @staticmethod
    def serialize(event: DistributedEvent) -> str:
        try:
            return event.model_dump_json()
        except Exception as e:
            logger.error(f"EventSerializer: Serialization failed: {e}")
            raise

    @staticmethod
    def deserialize(data: str) -> DistributedEvent:
        try:
            return DistributedEvent.model_validate_json(data)
        except Exception as e:
            logger.error(f"EventSerializer: Deserialization failed: {e}")
            raise

    @staticmethod
    def wrap_local_event(event_name: str, payload: Any, origin_node: str, chip_context: Optional[str] = None) -> DistributedEvent:
        import uuid
        return DistributedEvent(
            event_id=str(uuid.uuid4()),
            event_name=event_name,
            origin_node=origin_node,
            chip_context=chip_context,
            payload=payload
        )

event_serializer = EventSerializer()
