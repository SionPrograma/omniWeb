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

    async def execute_proposal(self, proposal_id: int) -> dict:
        """
        Executes a saved proposal through the Stability Loop.
        """
        from backend.core.stability_loop.loop_controller import loop_controller
        from backend.core.stability_loop.loop_models import LoopStep
        
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                proposal = conn.execute(
                    "SELECT * FROM improvement_proposals WHERE id = ?", (proposal_id,)
                ).fetchone()
                
        if not proposal:
            return {"status": "error", "message": "Proposal not found"}
            
        async def execution_action():
            # In a real system, this would parse 'recommended_action' and call the right module
            # For now, we simulate the action and mark it as completed
            logger.info(f"Executing improvement: {proposal['description']}")
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute(
                        "UPDATE improvement_proposals SET status = 'completed' WHERE id = ?",
                        (proposal_id,)
                    )
                    conn.commit()
            return {"status": "success", "action": proposal["recommended_action"]}

        loop_state, result = await loop_controller.execute_task(
            "improvement_proposal",
            execution_action,
            {"proposal_id": proposal_id, "description": proposal["description"]}
        )
        
        if loop_state.current_step == LoopStep.COMPLETE:
            return {"status": "success", "message": "Propuesta ejecutada y sistema estable.", "loop_id": loop_state.task_id}
        else:
            return {"status": "error", "message": f"Fallo en la ejecución o inestabilidad: {loop_state.current_step}", "loop_id": loop_state.task_id}

proposal_engine = ProposalEngine()
