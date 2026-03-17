import logging
import asyncio
from typing import List, Dict, Any, Optional
from .task_decomposer import task_decomposer, ShadowJob
from .execution_swarm import execution_swarm
from .audit_loop import audit_loop
from .knowledge_sync import knowledge_sync

logger = logging.getLogger(__name__)

class ShadowOrchestrator:
    """
    Coordinates the Shadow Swarm. 
    Manages decomposition, parallel execution, and synchronization.
    """
    
    def __init__(self):
        self.active_swarms: Dict[str, List[ShadowJob]] = {}

    async def execute_mission(self, goal: str, context: Dict[str, Any]) -> Dict[str, Any]:
        logger.info(f"[ORCHESTRATOR] Initializing Cognitive Extension Mission: {goal}")
        
        # 1. DECOMPOSE
        jobs = task_decomposer.decompose(goal, context)
        swarm_id = f"swarm_{id(jobs)}"
        self.active_swarms[swarm_id] = jobs
        
        # Track mission in conversation context
        from ..intent_understanding.conversation_tracker import conversation_tracker
        session_id = context.get("session_id", "default")
        conversation_tracker.set_mission(session_id, goal, swarm_id)
        
        # 2. DISPATCH (Dependency-Aware Wave Dispatching)
        # This wave dispatcher handles all job types (Sim, Exec, Audit, Learn, Sync) 
        # based on their explicit dependencies.
        pending_jobs = list(jobs)
        completed_ids = set()
        
        while pending_jobs:
            # Find jobs with all dependencies met
            ready_jobs = [
                j for j in pending_jobs 
                if all(dep in completed_ids for dep in j.dependencies)
            ]
            
            if not ready_jobs:
                logger.error(f"[ORCHESTRATOR] Circular dependency detected or unmet requirements. Aborting.")
                break
                
            logger.info(f"[ORCHESTRATOR] Dispatching Wave: {[j.id for j in ready_jobs]}")
            
            # Execute current wave in parallel
            await asyncio.gather(*[self._process_job(j) for j in ready_jobs])
            
            # Move to next wave
            for j in ready_jobs:
                completed_ids.add(j.id)
                pending_jobs.remove(j)
        
        # 3. KNOWLEDGE SYNC (Already handled in waves if synchronize is last)
        # But we keep it as a final safety if needed, or rely on the sync job at the end of the chain
        
        # 5. SYNTHESIZE
        results = {j.type.value: j.result for j in jobs}
        
        self.active_swarms.pop(swarm_id, None)
        return {
            "status": "success",
            "goal": goal,
            "jobs_executed": len(jobs),
            "results": results,
            "swarm_id": swarm_id
        }

    async def _process_job(self, job: ShadowJob):
        job.status = "executing"
        try:
            # Special handling for Audit/Sync could go here or inside swarm
            result = await execution_swarm.run_job(job)
            job.result = result
            job.status = "completed"
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Job {job.id} failed: {e}")
            job.status = "failed"
            job.result = {"error": str(e)}

shadow_orchestrator = ShadowOrchestrator()
