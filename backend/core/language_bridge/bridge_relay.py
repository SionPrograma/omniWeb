from typing import Dict, List
from .language_bridge_models import Utterance
from backend.core.event_bus import event_bus

class BridgeRelay:
    def __init__(self):
        self.global_buffer: Dict[str, List[Utterance]] = {} # session_id: utterances

    def relay_utterance(self, session_id: str, utterance: Utterance):
        """Broadcasts a translated utterance to the distributed network."""
        if session_id not in self.global_buffer:
            self.global_buffer[session_id] = []
        
        self.global_buffer[session_id].append(utterance)
        
        # Share with others
        event_bus.publish("bridge_utterance_relay", {
            "session_id": session_id,
            "utterance": utterance.model_dump(),
            "timestamp": utterance.timestamp.isoformat()
        })

    def handle_remote_utterance(self, data: dict):
        """Callback for receiving utterances from other nodes."""
        session_id = data.get("session_id")
        raw_u = data.get("utterance")
        if session_id and raw_u:
            u = Utterance(**raw_u)
            if session_id not in self.global_buffer:
                self.global_buffer[session_id] = []
            self.global_buffer[session_id].append(u)

bridge_relay = BridgeRelay()
