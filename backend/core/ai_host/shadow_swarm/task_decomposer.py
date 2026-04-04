import logging
from typing import List, Dict, Any, Optional
from pydantic import BaseModel
from enum import Enum

logger = logging.getLogger(__name__)

class MicrotaskType(Enum):
    UI_ARCHITECTURE = "ui_architecture"
    DATA_MODEL = "data_model"
    BUSINESS_LOGIC = "business_logic"
    INTEGRATION = "integration"
    TESTING = "testing"
    BUILD_PIPELINE = "build_pipeline"
    SIMULATION = "simulation"
    AUDIT = "audit"
    LEARNING = "learning"
    SYNCHRONIZE = "synchronize"

class ShadowJob(BaseModel):
    id: str
    type: MicrotaskType
    description: str
    context: Dict[str, Any]
    dependencies: List[str] = []
    status: str = "pending" # pending, executing, completed, failed
    result: Optional[Any] = None

class TaskDecomposer:
    """
    Decomposes complex objectives into independent microtasks (Shadow Jobs).
    These jobs can be executed in parallel by the Shadow Swarm.
    """
    
    def __init__(self):
        self.counter = 0

    def decompose(self, goal: str, context: Dict[str, Any]) -> List[ShadowJob]:
        # 0. Check for Mission Plan in context
        if "mission_plan" in context:
            return self.decompose_from_plan(context["mission_plan"], context)

        logger.info(f"[DECOMPOSER] Decomposing complex goal: {goal}")
        
        jobs = []
        
        # 1. OPTIONAL: SIMULATION TASK
        sim_job = ShadowJob(
            id=f"job_{self._next_id()}",
            type=MicrotaskType.SIMULATION,
            description=f"Simulate impact and risks for: {goal}",
            context=context
        )
        jobs.append(sim_job)
        
        # 2. ANALYZE GOAL FOR EXECUTION DOMAINS
        domains = self._analyze_domains(goal, context)
        exec_jobs = []
        for domain in domains:
            job = self._create_job(domain, goal, context)
            job.dependencies = [sim_job.id] # Execution depends on simulation sanity check
            exec_jobs.append(job)
            
        jobs.extend(exec_jobs)
            
        # 3. ADD AUDIT TASK
        audit_job = ShadowJob(
            id=f"job_{self._next_id()}",
            type=MicrotaskType.AUDIT,
            description=f"Distributed audit for: {goal}",
            context=context,
            dependencies=[j.id for j in exec_jobs]
        )
        jobs.append(audit_job)
        
        # 4. ADD LEARNING TASK
        learn_job = ShadowJob(
            id=f"job_{self._next_id()}",
            type=MicrotaskType.LEARNING,
            description=f"Extract success/failure patterns from: {goal}",
            context=context,
            dependencies=[audit_job.id]
        )
        jobs.append(learn_job)
        
        # 5. ADD SYNC TASK
        sync_job = ShadowJob(
            id=f"job_{self._next_id()}",
            type=MicrotaskType.SYNCHRONIZE,
            description="Synchronize swarm findings to Central Mind",
            context=context,
            dependencies=[learn_job.id]
        )
        jobs.append(sync_job)
        
        return jobs

    def decompose_from_plan(self, plan: Dict[str, Any], context: Dict[str, Any]) -> List[ShadowJob]:
        """Converts a structured MissionPlan into ShadowJobs."""
        logger.info(f"[DECOMPOSER] Decomposing mission from structured plan.")
        jobs = []
        
        # Mapping mission step types to microtask types
        type_map = {
            "analysis": MicrotaskType.BUSINESS_LOGIC,
            "simulation": MicrotaskType.SIMULATION,
            "execution": MicrotaskType.BUSINESS_LOGIC,
            "audit": MicrotaskType.AUDIT
        }
        
        for step in plan.get("steps", []):
            mtype = type_map.get(step.get("type"), MicrotaskType.BUSINESS_LOGIC)
            # Merge main context with step-specific context if provided
            job_ctx = context.copy()
            if "context" in step:
                job_ctx.update(step["context"])

            job = ShadowJob(
                id=f"plan_job_{step.get('id')}",
                type=mtype,
                description=step.get("description"),
                context=job_ctx,
                dependencies=[f"plan_job_{d}" for d in step.get("dependencies", [])]
            )
            jobs.append(job)
            
        # Ensure final sync job
        sync_job = ShadowJob(
            id=f"job_{self._next_id()}",
            type=MicrotaskType.SYNCHRONIZE,
            description="Synchronize plan findings to Central Mind",
            context=context,
            dependencies=[jobs[-1].id] if jobs else []
        )
        jobs.append(sync_job)
        
        return jobs

    def _analyze_domains(self, goal: str, context: Optional[Dict[str, Any]] = None) -> List[MicrotaskType]:
        # Improved logic: pick domains based on keywords and visual context (Phase 21)
        domains = []
        g = goal.lower()
        context = context or {}
        v_ctx = context.get("visual_context", {})
        hyp = v_ctx.get("hypothesis", {})
        
        # 1. Visual Context Priority
        if hyp:
            layer = hyp.get("layer", "").lower()
            if "ui" in layer or "frontend" in layer:
                if MicrotaskType.UI_ARCHITECTURE not in domains:
                    domains.append(MicrotaskType.UI_ARCHITECTURE)
            
        # 2. Text Keyword Priority
        if "crea" in g or "app" in g or "interfaz" in g or "ui" in g:
            if MicrotaskType.UI_ARCHITECTURE not in domains:
                domains.append(MicrotaskType.UI_ARCHITECTURE)
        if "datos" in g or "db" in g or "model" in g:
            domains.append(MicrotaskType.DATA_MODEL)
        if "lógica" in g or "logic" in g or "proceso" in g:
            domains.append(MicrotaskType.BUSINESS_LOGIC)
        if "integra" in g or "api" in g or "servicio" in g:
            domains.append(MicrotaskType.INTEGRATION)
            
        # Default safety: always at least business logic
        if not domains:
            domains.append(MicrotaskType.BUSINESS_LOGIC)
            
        return domains

    def _create_job(self, mtype: MicrotaskType, goal: str, context: Dict[str, Any]) -> ShadowJob:
        descriptions = {
            MicrotaskType.UI_ARCHITECTURE: f"Design UI components and layout for {goal}",
            MicrotaskType.DATA_MODEL: f"Define data structures and schemas for {goal}",
            MicrotaskType.BUSINESS_LOGIC: f"Implement core logic and rules for {goal}",
            MicrotaskType.INTEGRATION: f"Plan external integrations and API endpoints for {goal}",
        }
        
        # Phase 21: Auto-Targeting via Visual Hypothesis
        v_ctx = context.get("visual_context", {})
        hyp = v_ctx.get("hypothesis", {})
        suggested = hyp.get("suggested_paths", [])
        
        job_ctx = context.copy()
        if suggested and mtype in [MicrotaskType.UI_ARCHITECTURE, MicrotaskType.AUDIT]:
            job_ctx["target_file"] = suggested[0] # Focus on first relevant path
            job_ctx["radius"] = "localized"
        
        return ShadowJob(
            id=f"job_{self._next_id()}",
            type=mtype,
            description=descriptions.get(mtype, f"Process {mtype.value} for {goal}"),
            context=job_ctx
        )

    def _next_id(self) -> int:
        self.counter += 1
        return self.counter

task_decomposer = TaskDecomposer()
