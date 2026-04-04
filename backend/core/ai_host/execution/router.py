from fastapi import APIRouter, Security, HTTPException, Depends
from typing import List, Dict, Any, Optional
from .copilot_engine import copilot_engine, CopilotActionPlan
from .builder_engine import builder_execution_engine, BuilderTask, BuilderStatus
from backend.core.permissions import enforce_permission, set_chip_context
from backend.core.auth import get_current_user, OmniUser
from backend.core.master_logbook.manager import master_logbook_manager
from ..processors.multimodal_report import multimodal_report_generator

router = APIRouter()

@router.post("/plan", response_model=CopilotActionPlan)
async def create_plan(payload: Dict[str, Any], current_user: OmniUser = Depends(get_current_user)):
    """
    Generates an action plan from a creator prompt.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        prompt = payload.get("prompt")
        evidence = payload.get("multimodal_evidence", [])
        
        if not prompt and not evidence:
            raise HTTPException(status_code=400, detail="Missing prompt or evidence")
            
        plan = await copilot_engine.generate_plan(prompt, multimodal_evidence=evidence)
        
        # ENFORCE COGNITIVE PIPELINE
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        
        raw_res = AICommandResponse(
            intent="copilot_plan",
            status="success",
            message=plan.summary or f"He trazado un plan para: {prompt[:30]}...",
            payload=plan.dict()
        )
        
        unified = await orchestrator.orchestrate(
            message=prompt or "generate plan",
            understanding={"mode": "reflective_analysis", "intent_group": "ANALYSIS_INTENT"},
            context={"user_id": current_user.id},
            raw_response=raw_res
        )
        return {"status": "success", "payload": unified.model_dump()}

@router.post("/execute-step")
async def execute_step(payload: Dict[str, str], current_user: OmniUser = Depends(get_current_user)):
    """
    Executes a single step from an approved plan.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        plan_id = payload.get("plan_id")
        step_id = payload.get("step_id")
        
        if not plan_id or not step_id:
            raise HTTPException(status_code=400, detail="Missing plan_id or step_id")
            
        result = await copilot_engine.execute_step(plan_id, step_id)
        
        # ENFORCE COGNITIVE PIPELINE
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        
        msg = result.get("message", "Paso ejecutado correctamente.")
        raw_res = AICommandResponse(
            intent="execute_step",
            status="success" if result.get("success") else "failed",
            message=msg,
            payload=result
        )
        
        unified = await orchestrator.orchestrate(
            message=f"execute step {step_id}",
            understanding={"mode": "action_execution", "intent_group": "BUILD_INTENT"},
            context={"user_id": current_user.id},
            raw_response=raw_res
        )
        return {"status": "success", "payload": unified.model_dump()}

@router.get("/plan/{plan_id}", response_model=CopilotActionPlan)
async def get_plan(plan_id: str, current_user: OmniUser = Depends(get_current_user)):
    """
    Retrieves the current state of a plan.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        plan = copilot_engine.active_plans.get(plan_id)
        if not plan:
            raise HTTPException(status_code=404, detail="Plan not found")
        return plan

@router.get("/builder/task/{task_id}", response_model=BuilderTask)
async def get_builder_task(task_id: str, current_user: OmniUser = Depends(get_current_user)):
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        task = await builder_execution_engine.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

@router.get("/builder/mutations/{task_id}")
async def get_builder_mutations(task_id: str, current_user: OmniUser = Depends(get_current_user)):
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from .mutation_engine import mutation_engine
        mutations = mutation_engine.get_batch_by_task(task_id)
        return [m.dict() for m in mutations]

@router.get("/builder/active", response_model=List[BuilderTask])
async def get_active_builder_tasks(current_user: OmniUser = Depends(get_current_user)):
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        # Return tasks that are currently being processed in memory
        return list(builder_execution_engine.active_tasks.values())

@router.get("/builder/status/{task_id}", response_model=BuilderTask)
async def get_builder_status(task_id: str, current_user: OmniUser = Depends(get_current_user)):
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        task = await builder_execution_engine.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        return task

@router.post("/builder/control/{task_id}")
async def control_builder_task(task_id: str, action: str, current_user: OmniUser = Depends(get_current_user)):
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        task = await builder_execution_engine.get_task(task_id)
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        msg = ""
        if action == "retry":
            if task.current_module_id:
                await builder_execution_engine.retry_module(task_id, task.current_module_id)
                msg = "Module retry initiated"
            else:
                msg = "No module to retry"
        elif action == "cancel":
            task.status = BuilderStatus.CANCELLED
            await builder_execution_engine._persist_task(task)
            msg = "Task cancelled"
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")
            
        # ENFORCE COGNITIVE PIPELINE
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        
        raw_res = AICommandResponse(
            intent="builder_control",
            status="success",
            message=msg,
            payload={"task_id": task_id, "action": action}
        )
        
        unified = await orchestrator.orchestrate(
            message=f"builder {action} {task_id}",
            understanding={"mode": "direct_response", "intent_group": "SYSTEM"},
            context={"user_id": current_user.id},
            raw_response=raw_res
        )
        return {"status": "success", "payload": unified.model_dump()}

@router.get("/builder/preview/{preview_id}")
async def get_preview(preview_id: str, current_user: OmniUser = Depends(get_current_user)):
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from .patch_preview import patch_preview_engine
        preview = await patch_preview_engine.get_preview(preview_id)
        if not preview:
            raise HTTPException(status_code=404, detail="Preview not found")
        return preview

@router.post("/builder/preview/{preview_id}/decide")
async def decide_preview(preview_id: str, approved: bool, current_user: OmniUser = Depends(get_current_user)):
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from .patch_preview import patch_preview_engine
        from .mutation_engine import mutation_engine
        
        preview = await patch_preview_engine.get_preview(preview_id)
        if not preview:
            raise HTTPException(status_code=404, detail="Preview not found")
        reloaded_list = []
        res_bool = False
        if approved:
            # Apply mutation
            res_bool, reloaded_list = await mutation_engine.execute_batch(preview.batch)
            
            # Update task/module status
            task = await builder_execution_engine.get_task(preview.task_id)
            if task:
                module = next((m for m in task.modules if m.id == preview.module_id), None)
                if module:
                    module.status = BuilderStatus.COMPLETED
                    module.progress = 100.0
                    module.result = {"success": res_bool, "hot_reload": reloaded_list}
                    await builder_execution_engine._persist_module(module)
                    
                    # Continue execution loop
                    import asyncio
                    asyncio.create_task(builder_execution_engine._execute_loop(task))
        
        # ENFORCE COGNITIVE PIPELINE
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        
        raw_res = AICommandResponse(
            intent="preview_decide",
            status="success",
            message="Patch applied successfully" if approved else "Patch rejected",
            payload={"approved": approved, "reload_results": reloaded_list if approved else None}
        )
        
        unified = await orchestrator.orchestrate(
            message=f"approve preview {preview_id}" if approved else f"reject preview {preview_id}",
            understanding={"mode": "direct_response", "intent_group": "SYSTEM"},
            context={"user_id": current_user.id},
            raw_response=raw_res
        )
        return {"status": "success", "payload": unified.model_dump()}

@router.get("/mission/{mission_id}/report")
async def get_multimodal_mission_report(mission_id: str, current_user: OmniUser = Depends(get_current_user)):
    """
    CAPA 2 & 5: Visualizing consolidated multimodal mission history.
    Provides the 'Narrative' of a mission from first capture to final fix.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        report = multimodal_report_generator.generate_report(mission_id)
        if not report:
            raise HTTPException(status_code=404, detail="Mission report not found.")
        
        return {"status": "success", "report": report}

@router.get("/mission/{mission_id}/briefing")
async def get_mission_executive_briefing(mission_id: str, current_user: OmniUser = Depends(get_current_user)):
    """
    PHASE 54: MISSION HANDOFF COHERENCE.
    Returns a professional executive briefing with Markdown export.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from backend.core.ai_host.memory.mission_manager import mission_manager
        
        handoff = mission_manager.get_mission_handoff(mission_id)
        if not handoff:
            raise HTTPException(status_code=404, detail="Mission briefing not available.")
            
        return {
            "status": "success", 
            "handoff": handoff.model_dump(),
            "exportable_markdown": handoff.to_markdown()
        }

@router.post("/mission/{mission_id}/recall/validate")
async def validate_multimodal_recall(
    mission_id: str, 
    snapshot_id: str, 
    approved: bool, 
    reason: Optional[str] = None,
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 58: HUMAN FEEDBACK LOOP.
    Allows Creator to approve/reject a recovered memory.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from backend.core.ai_host.memory.mission_manager import mission_manager
        
        active = mission_manager.get_active_mission()
        if not active or active.mission_id != mission_id:
             raise HTTPException(status_code=404, detail="Active mission match failed.")
             
        success = active.validate_archival_recall(snapshot_id, approved, reason)
        if not success:
             raise HTTPException(status_code=404, detail="Snapshot not found or not indexed for recall.")
             
        mission_manager.save_mission(active)
        return {"status": "success", "validated_snapshot": snapshot_id, "approved": approved}

@router.post("/mission/{mission_id}/recall/reactivate")
async def reactivate_multimodal_recall(
    mission_id: str, 
    snapshot_id: str, 
    active: bool, 
    reason: Optional[str] = None,
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 59: MANUAL RE-FOCUS.
    Allows Creator to manually force/remove a storage snapshot into active context.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from backend.core.ai_host.memory.mission_manager import mission_manager
        
        m = mission_manager.get_active_mission()
        if not m or m.mission_id != mission_id:
             raise HTTPException(status_code=404, detail="Active mission match failed.")
             
        success = m.reactivate_archival_snapshot(snapshot_id, active, reason)
        if not success:
             raise HTTPException(status_code=404, detail="Snapshot not found in mission history.")
             
        mission_manager.save_mission(m)
        return {"status": "success", "snapshot_id": snapshot_id, "active": active}

@router.get("/mission/{mission_id}/archive/search")
async def search_mission_archive(
    mission_id: str, 
    query: Optional[str] = None, 
    layer: Optional[str] = None,
    issue_type: Optional[str] = None,
    status: Optional[str] = None,
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 60: DEEP ARCHIVE SEARCH.
    Search historical multimodal nodes by text or technical filters.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from backend.core.ai_host.memory.mission_manager import mission_manager
        
        m = mission_manager.get_mission(mission_id)
        if not m:
             raise HTTPException(status_code=404, detail="Mission not found.")
             
        filters = {
            "layer": layer,
            "issue_type": issue_type,
            "status": status
        }
        # Clear None filters
        filters = {k: v for k, v in filters.items() if v is not None}
        
        results = m.search_multimodal_archive(query=query, filters=filters)
        return {"status": "success", "count": len(results), "results": results}

@router.get("/mission/{mission_id}/drift")
async def get_mission_drift(
    mission_id: str, 
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 61: COGNITIVE DRIFT AUDIT.
    Returns alignment analysis between goals and current technical focus.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from backend.core.ai_host.memory.mission_manager import mission_manager
        
        m = mission_manager.get_mission(mission_id)
        if not m:
             raise HTTPException(status_code=404, detail="Mission not found.")
             
        drift_report = m.analyze_cognitive_drift()
        return {"status": "success", "report": drift_report}

@router.get("/portfolio/drift/health")
async def get_portfolio_drift_health(
    limit: int = 10,
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 63: PORTFOLIO DRIFT ANALYTICS.
    Aggregate cognitive alignment across all missions for portfolio oversight.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from backend.core.ai_host.memory.mission_manager import mission_manager
        
        health_portfolio = mission_manager.get_portfolio_cognitive_health(limit=limit)
        return {"status": "success", "count": len(health_portfolio), "portfolio": health_portfolio}

@router.get("/portfolio/drift/alerts")
async def get_drift_alerts(
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 64: COGNITIVE DRIFT ALERTS.
    Tactical notifications for missions crossing drift thresholds.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from backend.core.ai_host.memory.mission_manager import mission_manager
        
        pending_alerts = mission_manager.get_drift_alerts()
        return {"status": "success", "count": len(pending_alerts), "alerts": pending_alerts}

@router.post("/mission/{mission_id}/drift/correct")
async def execute_drift_correction(
    mission_id: str,
    action: Dict[str, Any],
    current_user: OmniUser = Depends(get_current_user)
):
    """
    PHASE 65: TACTICAL REALIGNMENT EXECUTION.
    Execute human-authorized corrective actions for cognitive drift.
    """
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from backend.core.ai_host.memory.mission_manager import mission_manager
        
        m = mission_manager.get_mission(mission_id)
        if not m:
             raise HTTPException(status_code=404, detail="Mission not found")
             
        result = m.execute_realignment_action(action)
        if result["success"]:
             mission_manager.save_mission(m)
             
        return {"status": "success" if result["success"] else "error", "result": result}
