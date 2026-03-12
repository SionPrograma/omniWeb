from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from backend.core.distributed_bus.node_registry import node_registry
from backend.core.event_bus import event_bus

class CommPacket(BaseModel):
    id: str
    sender_id: str
    recipient_id: str # Can be 'global'
    content: str
    timestamp: datetime = datetime.now()
    protocol: str = "P2P" # P2P, Broadcast, Relay

class GlobalCommunicationLayer:
    def __init__(self):
        self.message_log: List[CommPacket] = []

    def send_global_message(self, sender_id: str, content: str):
        packet = CommPacket(
            id=str(datetime.now().timestamp()),
            sender_id=sender_id,
            recipient_id="global",
            content=content,
            protocol="Broadcast"
        )
        self.message_log.append(packet)
        event_bus.publish("global_comm_message", packet.model_dump())
        return packet

    def receive_message(self, packet_data: dict):
        packet = CommPacket(**packet_data)
        self.message_log.append(packet)
        # Here we could trigger AI Host notifications
        return packet

global_comm = GlobalCommunicationLayer()
