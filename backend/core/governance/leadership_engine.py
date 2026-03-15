import logging
from typing import List, Dict, Any
from backend.core.governance.manager import governance_manager
from backend.core.user_memory_timeline.manager import timeline_manager
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context

logger = logging.getLogger(__name__)

class LeadershipDetectionEngine:
    """
    Analyzes user behavioral signals to detect potential leaders.
    Phase 3: Automatic Leadership Detection.
    """

    async def analyze_users(self):
        """Main loop to analyze all active users."""
        logger.info("Starting leadership detection analysis...")
        
        users = self._get_active_users()
        for user_id in users:
            signals = self._collect_signals(user_id)
            score = self._calculate_leadership_score(signals)
            
            if score >= 0.8: # Threshold for Admin Candidate recommendation
                self._recommend_promotion(user_id, signals)

    def _get_active_users(self) -> List[str]:
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("SELECT id FROM users WHERE is_active = 1").fetchall()
                return [row["id"] for row in rows]

    def _collect_signals(self, user_id: str) -> Dict[str, Any]:
        """Gathers behavioral data for a user."""
        timeline = timeline_manager.get_timeline(user_id)
        reputation = governance_manager.get_user_reputation_score(user_id)
        
        # Helper count (interactions where this user helped others)
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                help_row = conn.execute(
                    "SELECT COUNT(*) as count FROM reputation_graph_edges WHERE source_user_id = ? AND interaction_type = 'assistance'",
                    (user_id,)
                ).fetchone()
                helper_count = help_row["count"] or 0
                
                bug_reports = len([m for m in timeline if m.milestone_type == 'bug_report'])
                exploration = len([m for m in timeline if m.milestone_type == 'first_feature_exploration'])
                
        return {
            "reputation": reputation,
            "helper_count": helper_count,
            "bug_reports": bug_reports,
            "exploration_depth": exploration,
            "timeline_length": len(timeline)
        }

    def _calculate_leadership_score(self, signals: Dict[str, Any]) -> float:
        """Heuristic score based on weights."""
        score = 0.0
        score += min(signals["reputation"] * 0.1, 0.3)      # Up to 0.3 for reputation
        score += min(signals["helper_count"] * 0.05, 0.25)  # Up to 0.25 for helping
        score += min(signals["bug_reports"] * 0.1, 0.2)     # Up to 0.2 for feedback
        score += min(signals["exploration_depth"] * 0.05, 0.15) # Up to 0.15 for exploration
        score += min(signals["timeline_length"] * 0.01, 0.1)  # Up to 0.1 for longevity
        return score

    def _recommend_promotion(self, user_id: str, signals: Dict[str, Any]):
        """Creates a governance insight recommending promotion."""
        # Check if already recommended
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                existing = conn.execute(
                    "SELECT id FROM leadership_insights WHERE user_id = ? AND insight_type = 'leadership_detection' AND status = 'pending'",
                    (user_id,)
                ).fetchone()
                if existing:
                    return

        message = (
            f"User {user_id} shows strong leadership patterns. "
            f"Reputation: {signals['reputation']:.2f}, Help Count: {signals['helper_count']}, "
            f"Quality Feedback: {signals['bug_reports']}. "
            "Recommendation: Promote to Admin Candidate."
        )
        governance_manager.create_insight(user_id, message, "leadership_detection", metadata=signals)

leadership_engine = LeadershipDetectionEngine()
