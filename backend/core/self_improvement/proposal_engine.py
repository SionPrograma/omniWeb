import logging
from typing import List, Dict, Any
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .improvement_planner import improvement_planner

logger = logging.getLogger(__name__)

class ProposalEngine:
    """
    Saves and manages system improvement proposals.
    """
    def generate_proposals(self) -> int:
        """
        Runs the full analysis cycle and generates proposals.
        Returns the number of new proposals created.
        """
        plans = improvement_planner.plan_optimizations()
        new_count = 0
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                for plan in plans:
                    # Check if proposal already exists to avoid duplicates
                    exists = conn.execute(
                        "SELECT id FROM improvement_proposals WHERE description = ? AND status = 'pending'",
                        (plan["description"],)
                    ).fetchone()
                    
                    if not exists:
                        conn.execute(
                            """
                            INSERT INTO improvement_proposals (proposal_type, description, recommended_action)
                            VALUES (?, ?, ?)
                            """,
                            (plan["proposal_type"], plan["description"], plan["recommended_action"])
                        )
                        new_count += 1
                conn.commit()
        return new_count

    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """
        Returns a list of proposals awaiting user action.
        """
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT id, proposal_type, description, recommended_action, status, created_at FROM improvement_proposals WHERE status = 'pending' ORDER BY created_at DESC"
                ).fetchall()
                return [dict(r) for r in rows]

proposal_engine = ProposalEngine()
