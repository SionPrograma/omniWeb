from .logbook_models import Logbook
from typing import Dict

class LogbookSyncEngine:
    def __init__(self):
        self.remote_replicas: Dict[str, dict] = {} # node_id: {user_id: metadata}

    def broadcast_metadata(self, logbook: Logbook):
        """Prepare lightweight metadata for replication across the network."""
        metadata = {
            "id": logbook.id,
            "owner_id": logbook.owner_id,
            "topics": logbook.knowledge_topics,
            "skills": list(logbook.skills.keys()),
            "last_updated": logbook.last_updated.isoformat()
        }
        # In a real distributed scenario, this would be sent to the Event Bus
        return metadata

    def receive_metadata(self, node_id: str, metadata: dict):
        if node_id not in self.remote_replicas:
            self.remote_replicas[node_id] = {}
        self.remote_replicas[node_id][metadata["owner_id"]] = metadata

sync_engine = LogbookSyncEngine()
