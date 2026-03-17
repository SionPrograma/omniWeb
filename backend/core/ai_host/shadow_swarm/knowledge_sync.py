import logging
from typing import List, Dict, Any
from ..cognition.cognitive_core import cognitive_core
from ..memory.semantic_memory import semantic_memory

logger = logging.getLogger(__name__)

class KnowledgeSync:
    """
    Synchronizes shadow findings and mission outcomes back to the Central Mind.
    Ensures 'One Mind, Many Workers' principle.
    """
    
    async def synchronize(self, mission_goal: str, results: Dict[str, Any]):
        logger.info(f"[KNOWLEDGE_SYNC] Consolidating distributed findings for: {mission_goal}")
        
        # 1. Extract Structured Knowledge
        audit_res = results.get("audit", {})
        learning_res = results.get("learning", {})
        
        # 2. Update Cognitive Core with structured extension
        cognitive_core.record_execution_outcome(
            plan_id=f"swarm_{id(mission_goal)}",
            steps=[{"id": k, "desc": str(v)[:50]} for k, v in results.items()],
            outcome="COMPLETED" if audit_res.get("status") == "passed" else "PARTIAL",
            evidence=[
                f"swarm.integrity={audit_res.get('integrity_score', 0)}",
                f"swarm.patterns={len(learning_res.get('success_patterns', []))}"
            ]
        )
        
        # 3. Add to Semantic Memory as a Learning Interaction
        semantic_memory.add_interaction(
            f"MISSION_LEARNING: {mission_goal}",
            (
                f"Problem Type: Construction/Optimization\n"
                f"Solution Strategy: Distributed Swarm Execution\n"
                f"Patterns Extraction: {', '.join(learning_res.get('success_patterns', []))}\n"
                f"Audit Result: {audit_res.get('status')}"
            ),
            "swarm_orchestration"
        )
        
        logger.info("[KNOWLEDGE_SYNC] Cognitive extension sync complete. Perception expanded.")

knowledge_sync = KnowledgeSync()
