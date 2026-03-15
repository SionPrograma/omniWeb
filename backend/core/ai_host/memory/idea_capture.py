import logging
import uuid
import time
from typing import List, Dict, Optional, Any
from pydantic import BaseModel, Field
from .knowledge_graph import knowledge_graph

logger = logging.getLogger(__name__)

class IdeaEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: float = Field(default_factory=time.time)
    author: str = "creator"
    content: str
    tags: List[str] = []
    related_nodes: List[str] = [] # IDs of Knowledge Nodes

class IdeaCapture:
    """
    Handles the persistent capture of thoughts and ideas.
    """
    def __init__(self):
        self.ideas: Dict[str, IdeaEntry] = {}
        self._load_ideas()

    def _load_ideas(self):
        """
        Loads persisted ideas from SQLite into memory.
        """
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        import json

        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    rows = conn.execute("SELECT * FROM ai_host_ideas").fetchall()
                    for row in rows:
                        idea = IdeaEntry(
                            id=row["id"],
                            timestamp=row["timestamp"],
                            author=row["author"],
                            content=row["content"],
                            tags=json.loads(row["tags"]) if row["tags"] else [],
                            related_nodes=json.loads(row["related_nodes"]) if row["related_nodes"] else []
                        )
                        self.ideas[idea.id] = idea
            logger.info(f"[IDEA_LOAD] Loaded {len(self.ideas)} ideas from persistent storage.")
        except Exception as e:
            logger.error(f"[IDEA_LOAD_ERROR] Failed to load ideas: {e}")

    def capture_idea(self, text: str, source: str = "creator", tags: List[str] = []) -> IdeaEntry:
        """
        Main entry point for storing a raw thought.
        Also attempts to create a corresponding Knowledge Node if the idea is descriptive.
        """
        # 1. Create Idea Entry
        idea = IdeaEntry(
            content=text,
            author=source,
            tags=tags
        )
        
        # 2. Integration with Knowledge Graph (Phase 0 Polish)
        # We auto-create a node for every captured idea for now to ensure visibility
        node_title = text[:30] + "..." if len(text) > 30 else text
        node = knowledge_graph.store_knowledge_node(
            title=f"Idea: {node_title}",
            content=text,
            tags=["captured_idea"] + tags
        )
        idea.related_nodes.append(node.id)
        
        # 3. Store locally and in DB
        self.ideas[idea.id] = idea
        self._persist_idea(idea)
        
        # 4. Logbook Integration (Side Effect)
        self._log_to_system(idea)
        
        logger.info(f"[IDEA_CAPTURED] ID: {idea.id} | Content Preview: {text[:40]}...")
        return idea

    def _persist_idea(self, idea: IdeaEntry):
        from backend.core.database import db_manager
        from backend.core.permissions import set_chip_context
        import json
        try:
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO ai_host_ideas (id, timestamp, author, content, tags, related_nodes)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        idea.id, idea.timestamp, idea.author, idea.content,
                        json.dumps(idea.tags), json.dumps(idea.related_nodes)
                    ))
                    conn.commit()
        except Exception as e:
            logger.error(f"[IDEA_PERSIST_ERROR] {e}")

    def _log_to_system(self, idea: IdeaEntry):
        """
        Creates a logbook entry for the new idea.
        """
        try:
            # Avoid circular import by importing here
            from backend.core.system_auditor.auditor import auditor
            auditor.log_entry(
                "INFO",
                f"Idea captured by {idea.author}: {idea.content[:100]}",
                "ai-host",
                {"idea_id": idea.id, "type": "memory_event"}
            )
        except Exception as e:
            logger.warning(f"Could not log idea capture to auditor: {e}")

    def get_idea(self, idea_id: str) -> Optional[IdeaEntry]:
        return self.ideas.get(idea_id)

    def get_all_ideas(self) -> List[IdeaEntry]:
        return list(self.ideas.values())

    def search_ideas(self, query: str) -> List[IdeaEntry]:
        query = query.lower()
        return [i for i in self.ideas.values() if query in i.content.lower() or any(query in t.lower() for t in i.tags)]

idea_capture = IdeaCapture()
