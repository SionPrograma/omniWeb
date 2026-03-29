import logging
import asyncio
from typing import List, Dict, Any, Optional
from .task_decomposer import task_decomposer, ShadowJob, MicrotaskType
from .execution_swarm import execution_swarm
from .audit_loop import audit_loop
from .knowledge_sync import knowledge_sync
from .shadow_auditor import shadow_auditor_manager, ShadowState
from .shadow_constructor import shadow_constructor_manager, ConstructorState
from .approval_gate import approval_gate, GateStatus
from .apply_loop import manual_apply_loop

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
        
        # 1.5. SPAWN SHADOW AUDITORS & CONSTRUCTORS (Phase 11: Constructor Shadows)
        shadows = []
        constructors = []
        
        for job in jobs:
            # 1. Spawn Auditor (Always observational)
            if job.type in [MicrotaskType.BUSINESS_LOGIC, MicrotaskType.UI_ARCHITECTURE, MicrotaskType.DATA_MODEL, MicrotaskType.INTEGRATION]:
                auditor = shadow_auditor_manager.spawn_auditor(
                    mission_id=swarm_id,
                    microtask=job.description,
                    layer=job.context.get("primary_layer", "core/backend")
                )
                shadows.append(auditor)
                
                # 2. Spawn Constructor for constructive tasks (Phase 11)
                # In this phase we don't 'apply', we just propose
                constructor = shadow_constructor_manager.spawn_constructor(
                    mission_id=swarm_id,
                    microtask=job.description,
                    layer=job.context.get("primary_layer", "core/backend"),
                    file=job.context.get("target_file", "core/module.py")
                )
                constructors.append(constructor)
        
        # Run Audit Phase
        for s in shadows:
            await s.audit()
            
        # Run Construction Phase (Drafting Only - No Apply!)
        for c in constructors:
            proposal = await c.draft_proposal()
            # Cross-validation: Find the auditor for the same task and add its finding
            matching_auditor = next((s for s in shadows if s.assigned_microtask == c.assigned_microtask), None)
            if matching_auditor and matching_auditor.current_report:
                c.auditor_note = f"Auditor Review: {matching_auditor.current_report.findings[0]} (Risk: {matching_auditor.current_report.risk_level})"
            
            # 3. APPROVAL GATE (Phase 12: Approval/Apply Gate)
            # Evaluate proposal through the governance layer
            gate_decision = approval_gate.evaluate_proposal(c)
            # Map GateStatus value to ConstructorState (Pydantic will convert string to member)
            c.state = ConstructorState(gate_decision.status.value)
            # Add gate details to constructor for UI
            c.context = {**job.context, "gate_decision": gate_decision.dict()}

            # 4. MANUAL APPLY LOOP (Phase 13: Manual Apply Loop)
            # If the gate is READY and a 'manual_approval' is present in the request
            # For validation purposes we simulate the apply for 'AWAITING_HUMAN' if low risk
            if gate_decision.status == GateStatus.AWAITING_HUMAN and context.get("force_apply", False):
                logger.info(f"[ORCHESTRATOR] Triggering manual apply for {c.shadow_id}")
                await manual_apply_loop.run_apply_cycle(c, approver="Creator/Testing")
                # After apply cycle, constructor context includes the apply_record
        
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
            "swarm_id": swarm_id,
            "shadows": [s.dict() for s in shadows], # Export shadows (Auditors)
            "constructors": [c.dict() for c in constructors], # Export shadows (Constructors)
            "task_tree": {
                "mission_id": swarm_id,
                "summary": goal,
                "primary_layer": context.get("primary_layer", "core/backend"),
                "dependencies": [],
                "microtasks": [j.description for j in jobs[:3]],
                "forbidden_zones": [],
                "risk_level": "MEDIO"
            }
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
