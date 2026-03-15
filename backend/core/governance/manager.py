import json
import uuid
import logging
from typing import List, Optional
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .models import ReputationEdge, LeadershipInsight

logger = logging.getLogger(__name__)

class GovernanceManager:
    """
    Manages the Reputation Graph and Leadership Detection insights.
    Phases 2, 3, 4 of the Governance Expansion.
    """

    def record_interaction(self, source_id: str, target_id: str, interaction_type: str, trust_score: float = 0.1, metadata: dict = None):
        """Records a trust interaction between two users."""
        edge = ReputationEdge(
            id=str(uuid.uuid4()),
            source_user_id=source_id,
            target_user_id=target_id,
            interaction_type=interaction_type,
            trust_score=trust_score,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO reputation_graph_edges (id, source_user_id, target_user_id, interaction_type, trust_score, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (edge.id, edge.source_user_id, edge.target_user_id, edge.interaction_type, 
                     edge.trust_score, edge.timestamp.isoformat(), json.dumps(edge.metadata))
                )
                conn.commit()
        
        logger.info(f"Interaction recorded: {source_id} -> {target_id} ({interaction_type})")
        return edge

    def create_insight(self, user_id: str, message: str, insight_type: str = "leadership_detection", metadata: dict = None):
        """Generates an AI insight (leadership recommendation, etc.)"""
        insight = LeadershipInsight(
            id=str(uuid.uuid4()),
            user_id=user_id,
            insight_type=insight_type,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    """
                    INSERT INTO leadership_insights (id, user_id, insight_type, message, status, recommender, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (insight.id, insight.user_id, insight.insight_type, insight.message, 
                     insight.status, insight.recommender, insight.timestamp.isoformat(), json.dumps(insight.metadata))
                )
                conn.commit()
        
        logger.info(f"Governance insight created for user {user_id}: {insight_type}")
        return insight

    def get_pending_insights(self) -> List[LeadershipInsight]:
        """Retrieves all pending insights for the Creator/Admin review."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT * FROM leadership_insights WHERE status = 'pending'").fetchall()
                return [LeadershipInsight(
                    id=row["id"],
                    user_id=row["user_id"],
                    insight_type=row["insight_type"],
                    message=row["message"],
                    status=row["status"],
                    recommender=row["recommender"],
                    timestamp=datetime.fromisoformat(row["timestamp"]),
                    metadata=json.loads(row["metadata"]) if row["metadata"] else {}
                ) for row in rows]

    def get_user_reputation_score(self, user_id: str) -> float:
        """Calculates total reputation score for a user."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Sum of trust scores where user is the target
                row = conn.execute(
                    "SELECT SUM(trust_score) as total FROM reputation_graph_edges WHERE target_user_id = ?",
                    (user_id,)
                ).fetchone()
                return row["total"] or 0.0

governance_manager = GovernanceManager()
