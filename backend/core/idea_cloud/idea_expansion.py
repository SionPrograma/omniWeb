from typing import List, Optional
from backend.core.idea_cloud.idea_models import Idea, IdeaCluster
from backend.core.idea_cloud.idea_store import idea_store
from backend.core.logbook_network.logbook_manager import logbook_manager
from backend.core.logbook_network.logbook_models import EntryType
from backend.core.event_bus import event_bus

class IdeaCloudExpansion:
    async def process_new_idea(self, idea: Idea, owner_id: str = "default_user"):
        """
        Expanded processing for ideas:
        1. Link to Personal Logbook.
        2. Broadcast to Distributed Network.
        """
        # 1. Link to Logbook
        logbook_manager.add_entry(
            owner_id=owner_id,
            entry_type=EntryType.IDEA,
            content=idea.raw_thought,
            tags=idea.topics
        )
        
        # 2. Broadcast to Network via Event Bus
        event_bus.publish("global_idea_broadcast", {
            "idea_id": idea.id,
            "topics": idea.topics,
            "timestamp": idea.timestamp.isoformat(),
            "origin_id": "current_node"
        })
        
        return True

    def get_global_trends(self) -> List[str]:
        """Aggregate topics from all processed ideas and clusters."""
        clusters = idea_store.get_all_clusters()
        all_topics = []
        for c in clusters:
            all_topics.extend(c.name.split()) # Simplified trend detection
        return list(set(all_topics))

idea_expansion = IdeaCloudExpansion()
