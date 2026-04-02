import logging
import asyncio
import json
from typing import List, Dict, Any, Optional
from .task_decomposer import task_decomposer, ShadowJob, MicrotaskType
from .execution_swarm import execution_swarm
from .audit_loop import audit_loop
from .knowledge_sync import knowledge_sync
from .shadow_auditor import shadow_auditor_manager, ShadowState
from .shadow_constructor import shadow_constructor_manager, ConstructorState
from .approval_gate import approval_gate, GateStatus
from .apply_loop import manual_apply_loop

from .shadow_memory import shadow_memory_manager, TechnicalIncident, IncidentType
import uuid

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
        
        # 1.0 SCOPE FILTERING (Phase 19 & 21: Rich Constraints + Freeze)
        is_audit_only = context.get("audit_only", False)
        forbidden_p = context.get("forbidden_paths", [])
        forbidden_l = context.get("forbidden_layers", [])
        frozen_p = context.get("frozen_paths", [])
        frozen_l = context.get("frozen_layers", [])
        allowed_p = context.get("allowed_paths", [])

        filtered_jobs = []
        for job in jobs:
            target = job.context.get("target_file", "")
            primary_layer = job.context.get("primary_layer", "core/backend")
            
            # Check Frozen (PHASE 21)
            if any(p in target for p in frozen_p) or any(l in primary_layer or l in target for l in frozen_l):
                logger.info(f"[ORCHESTRATOR] Filtering OUT job {job.id} - SECTOR CONGELADO: {target}")
                continue

            # Check forbidden paths (PHASE 19)
            if any(p in target for p in forbidden_p):
                logger.info(f"[ORCHESTRATOR] Filtering OUT job {job.id} - Forbidden path: {target}")
                continue
            
            # Check forbidden layers
            if any(l in primary_layer or l in target for l in forbidden_l):
                logger.info(f"[ORCHESTRATOR] Filtering OUT job {job.id} - Forbidden layer: {primary_layer}")
                continue
            
            # Check allowed paths (If set, target MUST be in one of them)
            if allowed_p and not any(p in target for p in allowed_p):
                logger.info(f"[ORCHESTRATOR] Filtering OUT job {job.id} - Outside allowed scope: {target}")
                continue
            
            filtered_jobs.append(job)
        
        jobs = filtered_jobs
        self.active_swarms[swarm_id] = jobs
        
        # 1.1 SAFETY CHECKPOINT (Bloque: Mission Checkpoints)
        try:
            from ..memory.mission_manager import mission_manager
            active = mission_manager.get_active_mission()
            if active:
                 mission_manager.create_checkpoint(active.mission_id, f"Auto: Antes de Swarm {swarm_id}")
        except Exception as e:
            logger.warning(f"[ORCHESTRATOR] Failed to create auto-checkpoint: {e}")
        
        # Track mission in conversation context
        from ..intent_understanding.conversation_tracker import conversation_tracker
        session_id = context.get("session_id", "default")
        conversation_tracker.set_mission(session_id, goal, swarm_id)
        
        # 1.5. SPAWN SHADOW AUDITORS & CONSTRUCTORS (Phase 11: Constructor Shadows)
        shadows = []
        constructors = []
        is_audit_only = context.get("audit_only", False)
        
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
                # But SKIP if this is an audit-only mission (Phase 18)
                if not is_audit_only:
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
        # Skip if audit_only
        if not is_audit_only:
            for c in constructors:
                # Cross-validation: Find the auditor for the same task
                matching_auditor = next((s for s in shadows if s.assigned_microtask == c.assigned_microtask), None)
                
                # PROACTIVE INTEGRATION: Pass the audit report to the constructor BEFORE drafting
                audit_report = matching_auditor.current_report if matching_auditor else None
                proposal = await c.draft_proposal(audit_report=audit_report)
                
                if matching_auditor and matching_auditor.current_report:
                    c.auditor_note = f"Auditor Review: {matching_auditor.current_report.findings[0]} (Risk: {matching_auditor.current_report.risk_level})"
                
                # 3. APPROVAL GATE (Phase 12: Approval/Apply Gate)
                # If conservative_mode is on, we can artificially increase risk here or in the gate itself
                gate_decision = approval_gate.evaluate_proposal(c)
                # Map GateStatus value to ConstructorState (Pydantic will convert string to member)
                c.state = ConstructorState(gate_decision.status.value)
                
                # Store in job context for deep evidence tracking (Phase 17 Visibility)
                job.context["constructor_proposal"] = c.proposal.model_dump() if c.proposal else None
                job.context["gate_decision"] = gate_decision.dict()
                if matching_auditor and matching_auditor.current_report:
                    job.context["audit_findings"] = matching_auditor.current_report.dict()

                # Sync to Mission Tree if human intervention is needed
                if gate_decision.status == GateStatus.AWAITING_HUMAN:
                     from ..memory.mission_manager import mission_manager
                     mission_manager.update_step_status(job.id, "NEEDS_REVIEW", f"Bloqueado para revisión: {job.id}", evidence=f"Riesgo: {gate_decision.risk_score}", deep_evidence=job.context)

                # 4. MANUAL APPLY LOOP (Phase 13: Manual Apply Loop)
                if gate_decision.status == GateStatus.AWAITING_HUMAN and context.get("force_apply", False):
                    logger.info(f"[ORCHESTRATOR] Triggering manual apply for {c.shadow_id}")
                    await manual_apply_loop.run_apply_cycle(c, approver="Creator/Testing")
        else:
             logger.info("[ORCHESTRATOR] Skipping construction due to AUDIT_ONLY mode.")

        # 1.6 MULTI-AGENT CONFLICT RESOLUTION (NUEVO BLOQUE)
        # Skip if audit_only
        if not is_audit_only and constructors:
            from .conflict_resolver import conflict_resolver
            conflicts = conflict_resolver.detect_conflicts(constructors)
            
            if conflicts:
                logger.warning(f"[ORCHESTRATOR] Detected {len(conflicts)} Multi-Agent Conflicts in swarm {swarm_id}")
                
                # TRIGGER SELF-CORRECTION LOOP (NUEVO BLOQUE)
                logger.info(f"[ORCHESTRATOR] Triggering SELF-CORRECTION LOOP for swarm {swarm_id}")
                for conf in conflicts:
                    for sid in conf.shadow_ids:
                        c = next((cons for cons in constructors if cons.shadow_id == sid), None)
                        if c and not c.was_redrafted:
                            await c.redraft_proposal(feedback=f"CONFLICTO {conf.type.value}: {conf.explanation[:50]}")
                
                # Re-verify conflicts after redraft (Pass 2)
                conflicts = conflict_resolver.detect_conflicts(constructors)
                if conflicts:
                     logger.warning(f"[ORCHESTRATOR] Still {len(conflicts)} conflicts after redraft. Raising to Human REVIEW.")

                # Map conflicts/self-correction info to jobs to reflect in Mission Tree
                for conf in conflicts:
                    for sid in conf.shadow_ids:
                        # Find matching job
                        job = next((j for j in jobs if j.context.get("constructor_proposal", {}).get("shadow_id") == sid or sid in j.id), None)
                        if job:
                            job.context["multi_agent_conflict"] = conf.model_dump()
                            job.context["self_correction_applied"] = True
                            # Update mission status to reflect conflict
                            from ..memory.mission_manager import mission_manager
                            mission_manager.update_step_status(job.id, "NEEDS_REVIEW", f"CONFLICTO TRAS REDRAFT: {job.id}", evidence=f"Choque: {conf.type.value}", deep_evidence=job.context)
                
                # MEMORY WRITEBACK: Record conflict in historical memory
                for conf in conflicts:
                    shadow_memory_manager.record_incident(TechnicalIncident(
                        incident_id=f"inc_{uuid.uuid4().hex[:8]}",
                        mission_id=swarm_id,
                        target_path="multi_file" if len(conf.shadow_ids) > 1 else "single",
                        target_layer=context.get("primary_layer", "core/backend"),
                        incident_type=IncidentType.CONFLICT,
                        description=f"Persistent Conflict: {conf.explanation}",
                        severity="MEDIUM"
                    ))

        
        # 2. DISPATCH (Dependency-Aware Wave Dispatching)
        # SKIP dispatch entirely if audit_only (Phase 18)
        if is_audit_only:
             logger.info(f"[ORCHESTRATOR] Audit only mission {swarm_id} completed after observation pass.")
             return {
                 "status": "success",
                 "mode": "AUDIT_ONLY",
                 "goal": goal,
                 "jobs_executed": 0,
                 "results": {"audit": [s.current_report.dict() for s in shadows if s.current_report]},
                 "swarm_id": swarm_id,
                 "shadows": [s.dict() for s in shadows],
                 "constructors": []
             }

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
                "primary_layer": context.get("affected_layers", context.get("mission_intake", {}).get("affected_layers", ["core/backend"]))[0],
                "dependencies": [],
                "microtasks": [j.description for j in jobs],
                "forbidden_zones": context.get("risks", context.get("mission_intake", {}).get("risks", [])),
                "risk_level": "MEDIO" if not (context.get("risks") or context.get("mission_intake", {}).get("risks")) else "ALTO"
            }
        }

    async def _process_job(self, job: ShadowJob):
        job.status = "executing"
        from ..memory.mission_manager import mission_manager
        mission_manager.update_step_status(job.id, "ACTIVE", f"Shadow '{job.id}' iniciado...")
        
        try:
            # Special handling for Audit/Sync could go here or inside swarm
            result = await execution_swarm.run_job(job)
            job.result = result
            job.status = "completed"
            
            # Extract short evidence from result
            ev = str(result.get("summary", result.get("output", "Tarea finalizada")))[:60]
            
            # Deep Evidence: Merge results with initial findings (constructors, auditors)
            deep_ev = job.context.copy()
            if isinstance(result, dict): deep_ev.update(result)
            else: deep_ev["output"] = str(result)
            
            mission_manager.update_step_status(job.id, "COMPLETED", f"Shadow '{job.id}' termin con xito.", evidence=ev, deep_evidence=deep_ev)
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Job {job.id} failed: {e}")
            job.status = "failed"
            job.result = {"error": str(e)}
            mission_manager.update_step_status(job.id, "FAILED", f"Shadow '{job.id}' fall: {str(e)[:50]}...", evidence=f"Error: {str(e)[:40]}", deep_evidence={"error": str(e)})
            
            # MEMORY WRITEBACK: Record job failure
            shadow_memory_manager.record_incident(TechnicalIncident(
                incident_id=f"inc_{uuid.uuid4().hex[:8]}",
                mission_id=job.id.split("_")[0], # Approximate mission ID
                target_path=job.context.get("target_file", "unknown"),
                target_layer=job.context.get("primary_layer", "core/backend"),
                incident_type=IncidentType.FAILURE,
                description=f"Job failure: {str(e)[:100]}",
                severity="HIGH"
            ))

    async def rescue_step(self, step_id: str, mission_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Launches a context-aware rescue operation for a failed step.
        Uses Deep Evidence to inform the rescue strategy.
        """
        from ..memory.mission_manager import mission_manager
        mission = mission_manager.get_active_mission()
        if not mission: return {"status": "error", "message": "No active mission found"}
        
        # 1. Find node in tree
        def find_node(node, tid):
            if str(node.get('id')) == str(tid): return node
            for c in node.get('children', []):
                found = find_node(c, tid)
                if found: return found
            return None
            
        tree = mission.context_snap.get("tree")
        if not tree: return {"status": "error", "message": "Mission has no tree"}
        
        node = find_node(tree["root"], step_id)
        if not node: return {"status": "error", "message": f"Step {step_id} not found in tree"}
        
        logger.info(f"[ORCHESTRATOR] Initiating RESCUE for step {step_id}: {node['label']}")
        mission_manager.update_step_status(step_id, "RECOVERING", f"Iniciando RECOVERY para '{node['label']}'...")
        
        # 2. Build Rescue Job with Context
        from .task_decomposer import ShadowJob, MicrotaskType
        evidence = node.get("deep_evidence", {})
        error_info = evidence.get("error", evidence.get("output", "Unknown error"))
        
        rescue_job = ShadowJob(
            id=f"rescue_{step_id}_{id(node)}",
            type=MicrotaskType.BUSINESS_LOGIC, # High-level fix
            description=f"RESCUE: {node['label']}. REASON: {error_info[:100]}",
            dependencies=[],
            context={
                "original_step_id": step_id,
                "failure_evidence": evidence,
                "strategy": "SURGICAL_FIX"
            }
        )
        
        # 3. Execute through specialized Rescue Agent (or generic with rescue context)
        try:
            from .approval_gate import approval_gate, GateStatus
            
            # We use 'rescue' as a conceptual role in the swarm
            result = await execution_swarm.run_job(rescue_job, role="rescue")
            
            # 4. Governance check (Bloque 3 Integration)
            is_mutation = result.get("fix_applied", False) or "diff" in result
            gate_decision = None
            if is_mutation:
                 gate_decision = approval_gate.execute_governance_check(
                     intent=f"RESCUE: {node['label']}",
                     targets=result.get("affected_files", ["shadow_fix"]),
                     action_type="mutation",
                     risk_hint="MEDIUM",
                     proposal_id=rescue_job.id
                 )
            
            # 5. Success -> Update original node based on governance
            final_status = "COMPLETED"
            event_msg = f"Rescate de {step_id} EXITOSO."
            
            if gate_decision and gate_decision.status == GateStatus.AWAITING_HUMAN:
                final_status = "NEEDS_REVIEW"
                event_msg = f"Rescate de {step_id} REQUIERE REVISIÓN."
            
            mission_manager.update_step_status(
                step_id, 
                final_status, 
                event_msg, 
                evidence=f"Resultado: {str(result.get('summary', 'Ok'))[:50]}",
                deep_evidence={
                    **evidence, 
                    "rescue_result": result, 
                    "gate_decision": json.loads(gate_decision.model_dump_json()) if gate_decision else None,
                    "status": "repaired_pending" if final_status == "NEEDS_REVIEW" else "repaired"
                }
            )
            # MEMORY WRITEBACK: Record successful or review-pending rescue
            shadow_memory_manager.record_incident(TechnicalIncident(
                incident_id=f"inc_{uuid.uuid4().hex[:8]}",
                mission_id=mission.mission_id,
                target_path=node.get("target_file", "unknown_path"),
                target_layer=node.get("layer", "core/backend"),
                incident_type=IncidentType.RESCUE,
                description=f"Rescue applied for: {node['label']}",
                severity="LOW",
                resolution_applied="SURGICAL_FIX" if final_status == "COMPLETED" else "PENDING_APPROVAL"
            ))

            return {"status": "success", "result": result, "governance": gate_decision.dict() if gate_decision else None}
        except Exception as e:
            logger.error(f"[ORCHESTRATOR] Rescue failed: {e}")
            mission_manager.update_step_status(step_id, "FAILED", f"Rescate fall: {str(e)[:50]}...")
            return {"status": "error", "message": str(e)}

shadow_orchestrator = ShadowOrchestrator()
