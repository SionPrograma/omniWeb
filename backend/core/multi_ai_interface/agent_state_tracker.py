import logging
import time
from typing import Dict

logger = logging.getLogger(__name__)

class AgentStateTracker:
    """Tracks real-time connectivity and activity of external agents."""
    
    def __init__(self):
        self._last_heartbeats: Dict[str, float] = {}

    def record_activity(self, agent_id: str):
        self._last_heartbeats[agent_id] = time.time()

    def get_active_status(self, agent_id: str) -> bool:
        last = self._last_heartbeats.get(agent_id, 0)
        return (time.time() - last) < 60 # Active if heard within 60s

agent_state_tracker = AgentStateTracker()
