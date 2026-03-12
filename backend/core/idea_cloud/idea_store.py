import json
import logging
from typing import List, Optional
from datetime import datetime
from backend.core.database import db_manager
from .idea_models import Idea, IdeaCluster

logger = logging.getLogger(__name__)

class IdeaStore:
    """Handles persistent storage of divergent ideas and concept clusters."""

    def save_idea(self, idea: Idea):
        with db_manager.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO idea_cloud 
                   (id, raw_thought, timestamp, user_context, topics, sentiment, linked_nodes, linked_memories, is_processed, suggested_actions)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    idea.id,
                    idea.raw_thought,
                    idea.timestamp.isoformat(),
                    json.dumps(idea.user_context),
                    json.dumps(idea.topics),
                    idea.sentiment,
                    json.dumps(idea.linked_nodes),
                    json.dumps(idea.linked_memories),
                    1 if idea.is_processed else 0,
                    json.dumps(idea.suggested_actions)
                )
            )
            conn.commit()

    def get_unprocessed_ideas(self) -> List[Idea]:
        ideas = []
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM idea_cloud WHERE is_processed = 0").fetchall()
            for row in rows:
                ideas.append(self._row_to_idea(row))
        return ideas

    def get_recent_ideas(self, limit: int = 20) -> List[Idea]:
        ideas = []
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM idea_cloud ORDER BY timestamp DESC LIMIT ?", (limit,)).fetchall()
            for row in rows:
                ideas.append(self._row_to_idea(row))
        return ideas

    def _row_to_idea(self, row) -> Idea:
        return Idea(
            id=row["id"],
            raw_thought=row["raw_thought"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            user_context=json.loads(row["user_context"] or "{}"),
            topics=json.loads(row["topics"] or "[]"),
            sentiment=row["sentiment"] or 0.0,
            linked_nodes=json.loads(row["linked_nodes"] or "[]"),
            linked_memories=json.loads(row["linked_memories"] or "[]"),
            is_processed=bool(row["is_processed"]),
            suggested_actions=json.loads(row["suggested_actions"] or "[]")
        )

    def save_cluster(self, cluster: IdeaCluster):
        with db_manager.get_connection() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO idea_clusters 
                   (id, name, idea_ids, summary, emerging_project, last_updated)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    cluster.id,
                    cluster.name,
                    json.dumps(cluster.idea_ids),
                    cluster.summary,
                    1 if cluster.emerging_project else 0,
                    cluster.last_updated.isoformat()
                )
            )
            conn.commit()

    def get_all_clusters(self) -> List[IdeaCluster]:
        clusters = []
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM idea_clusters").fetchall()
            for row in rows:
                clusters.append(IdeaCluster(
                    id=row["id"],
                    name=row["name"],
                    idea_ids=json.loads(row["idea_ids"] or "[]"),
                    summary=row["summary"],
                    emerging_project=bool(row["emerging_project"]),
                    last_updated=datetime.fromisoformat(row["last_updated"])
                ))
        return clusters

idea_store = IdeaStore()
