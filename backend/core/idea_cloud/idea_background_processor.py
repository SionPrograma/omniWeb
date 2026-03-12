import logging
import asyncio
from typing import List, Dict, Any
from datetime import datetime
from .idea_store import idea_store
from .idea_models import Idea, IdeaCluster

logger = logging.getLogger(__name__)

class IdeaBackgroundProcessor:
    """Asynchronous engine for clustering related ideas and detecting emerging projects."""

    def __init__(self):
        self._running = False

    async def start(self):
        if self._running: return
        self._running = True
        asyncio.create_task(self._process_loop())
        logger.info("Idea Cloud: Background Processor started.")

    async def _process_loop(self):
        while self._running:
            try:
                await self._run_cycle()
            except Exception as e:
                logger.error(f"Idea Cloud: Error in background cycle: {e}")
            await asyncio.sleep(60) # Run every minute

    async def _run_cycle(self):
        unprocessed = idea_store.get_unprocessed_ideas()
        if not unprocessed: return
        
        logger.info(f"Idea Cloud: Processing {len(unprocessed)} new ideas...")
        
        # Simple Clustering by Topic
        all_ideas = idea_store.get_recent_ideas(limit=100)
        topic_map: Dict[str, List[str]] = {}
        
        for idea in all_ideas:
            for topic in idea.topics:
                if topic not in topic_map: topic_map[topic] = []
                topic_map[topic].append(idea.id)
        
        # Build Clusters for topics with > 2 ideas
        for topic, ids in topic_map.items():
            if len(ids) >= 2:
                cluster = IdeaCluster(
                    name=f"Project: {topic.capitalize()}",
                    idea_ids=ids,
                    summary=f"Emerging concept cluster based on {len(ids)} ideas related to {topic}.",
                    emerging_project=len(ids) >= 3
                )
                idea_store.save_cluster(cluster)
        
        # Mark as processed and trigger expansion
        from .idea_expansion import idea_expansion
        for idea in unprocessed:
            idea.is_processed = True
            idea_store.save_idea(idea)
            await idea_expansion.process_new_idea(idea)

idea_background_processor = IdeaBackgroundProcessor()
