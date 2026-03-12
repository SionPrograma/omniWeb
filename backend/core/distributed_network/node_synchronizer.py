from typing import Dict, Any
from backend.core.event_bus import event_bus

class NodeSynchronizer:
    def __init__(self):
        self.node_states: Dict[str, Any] = {}

    def broadcast_state_change(self, key: str, value: Any):
        """Broadcasts a local state change to all nodes."""
        event_bus.publish("node_state_update", {
            "key": key,
            "value": value,
            "origin": "current_node"
        })

    def handle_update(self, data: dict):
        origin = data.get("origin")
        key = data.get("key")
        value = data.get("value")
        if origin and key:
            if origin not in self.node_states:
                self.node_states[origin] = {}
            self.node_states[origin][key] = value

node_synchronizer = NodeSynchronizer()
