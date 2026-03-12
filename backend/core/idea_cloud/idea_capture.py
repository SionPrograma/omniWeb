import logging
from typing import Dict, Any, List, Optional
from .idea_models import Idea
from .idea_store import idea_store
from .idea_parser import idea_parser
from .idea_linker import idea_linker

logger = logging.getLogger(__name__)

class IdeaCapture:
    """Entry point for capturing free-form ideas from the user."""

    def capture(self, raw_thought: str, context: Optional[Dict[str, Any]] = None) -> Idea:
        """Processes a raw thought into a structured Idea and stores it."""
        logger.info(f"Idea Cloud: Capturing thought: {raw_thought[:50]}...")
        
        # 1. Basic Extraction
        topics = idea_parser.extract_topics(raw_thought)
        
        # 2. Find Links
        links = idea_linker.find_links(topics)
        
        # 3. Create Idea
        idea = Idea(
            raw_thought=raw_thought,
            user_context=context or {},
            topics=topics,
            linked_nodes=links["nodes"],
            linked_memories=links["memories"]
        )
        
        # 4. Save
        idea_store.save_idea(idea)
        
        return idea

idea_capture = IdeaCapture()
