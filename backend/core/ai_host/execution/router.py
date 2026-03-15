from fastapi import APIRouter, Security, HTTPException
from typing import List, Dict, Any
from .copilot_engine import copilot_engine, CopilotActionPlan
from .builder_engine import builder_execution_engine, BuilderTask, BuilderStatus
from backend.core.permissions import enforce_permission
from backend.core.master_logbook.manager import master_logbook_manager

router = APIRouter()

@router.post("/plan", response_model=CopilotActionPlan)
async def create_plan(payload: Dict[str, Any]):
    """
    Generates an action plan from a creator prompt.
    """
    enforce_permission("creator_access")
    prompt = payload.get("prompt")
    evidence = payload.get("multimodal_evidence", [])
    
    if not prompt and not evidence:
        raise HTTPException(status_code=400, detail="Missing prompt or evidence")
        
    plan = await copilot_engine.generate_plan(prompt, multimodal_evidence=evidence)
    return plan

@router.post("/execute-step")
async def execute_step(payload: Dict[str, str]):
    """
    Executes a single step from an approved plan.
    """
    enforce_permission("creator_access")
    plan_id = payload.get("plan_id")
    step_id = payload.get("step_id")
    
    if not plan_id or not step_id:
        raise HTTPException(status_code=400, detail="Missing plan_id or step_id")
        
    result = await copilot_engine.execute_step(plan_id, step_id)
    return result

@router.get("/plan/{plan_id}", response_model=CopilotActionPlan)
async def get_plan(plan_id: str):
    """
    Retrieves the current state of a plan.
    """
    enforce_permission("creator_access")
    plan = copilot_engine.active_plans.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    return plan

# --- Builder Execution Endpoints ---

@router.post("/builder/approve/{roadmap_id}")
async def approve_roadmap(roadmap_id: str):
    """
    Approves a roadmap entry and initializes an execution task.
    """
    enforce_permission("creator_access")
    
    # 1. Fetch from Master Logbook
    from backend.core.master_logbook.models import EntryType
    entries = master_logbook_manager.get_entries(limit=100) # Simple fetch
    target = next((e for e in entries if e.id == roadmap_id and e.type == EntryType.ROADMAP), None)
    
    if not target:
        raise HTTPException(status_code=404, detail="Roadmap entry not found")
        
    # 2. Initialize Task
    task = await builder_execution_engine.initialize_from_roadmap(target)
    
    return {"status": "success", "task_id": task.id, "message": "Roadmap approved. Execution task created."}

@router.post("/builder/start/{task_id}")
async def start_builder_task(task_id: str):
    """
    Begins execution of a builder task.
    """
    enforce_permission("creator_access")
    await builder_execution_engine.start_execution(task_id)
    return {"status": "success", "message": "Execution sequence engaged."}

@router.get("/builder/status/{task_id}")
async def get_builder_status(task_id: str):
    """
    Retrieves the current progress and status of a builder task.
    """
    enforce_permission("creator_access")
    task = builder_execution_engine.active_tasks.get(task_id)
    if not task:
        # Fallback: maybe load from DB? (For now just 404)
        raise HTTPException(status_code=404, detail="Active task not found")
        
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "progress": task.progress,
        "current_module_id": task.current_module_id,
        "modules": [
            {
                "id": m.id,
                "title": m.title,
                "status": m.status,
                "progress": m.progress,
                "type": m.module_type
            } for m in task.modules
        ]
    }

@router.get("/builder/mutations/{task_id}")
async def get_builder_mutations(task_id: str):
    """
    Retrieves all mutations associated with a builder task.
    """
    enforce_permission("creator_access")
    try:
        with db_manager.get_connection() as conn:
            rows = conn.execute("SELECT * FROM builder_mutations WHERE task_id = ? ORDER BY timestamp DESC", (task_id,)).fetchall()
            return [dict(r) for r in rows]
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/builder/preview/{preview_id}")
async def get_patch_preview(preview_id: str):
    enforce_permission("creator_access")
    from .patch_preview import patch_preview_engine
    preview = await patch_preview_engine.get_preview(preview_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Preview not found")
    return preview

@router.post("/builder/preview/{preview_id}/decide")
async def decide_patch_preview(preview_id: str, approved: bool):
    enforce_permission("creator_access")
    from .patch_preview import patch_preview_engine
    from .builder_engine import builder_execution_engine
    from .builder_models import BuilderStatus
    
    preview = await patch_preview_engine.get_preview(preview_id)
    if not preview:
        raise HTTPException(status_code=404, detail="Preview not found")
    
    success = await patch_preview_engine.decide(preview_id, approved)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to record decision")
    
    if approved:
        # Actually execute the mutation
        from .mutation_engine import mutation_engine
        mutation_success, reload_results = await mutation_engine.execute_batch(preview.batch)
        
        # Update task/module status and resume
        task = await builder_execution_engine.get_task(preview.task_id)
        if task:
            module = next((m for m in task.modules if m.id == preview.module_id), None)
            if module:
                if mutation_success:
                    module.status = BuilderStatus.COMPLETED
                    module.progress = 100.0
                    module.result = module.result or {}
                    module.result["hot_reload"] = reload_results
                else:
                    module.status = BuilderStatus.FAILED
                    module.error = "File mutation failed after preview approval"
                
                # Resume loop
                task.status = BuilderStatus.EXECUTING
                await builder_execution_engine.start_execution(task.id)
                
        return {"success": True, "mutation_executed": approved, "reload_results": reload_results}
    else:
        # Rejected
        task = await builder_execution_engine.get_task(preview.task_id)
        if task:
            module = next((m for m in task.modules if m.id == preview.module_id), None)
            if module:
                module.status = BuilderStatus.FAILED
                module.error = "Patch preview was rejected by Creator"
                task.status = BuilderStatus.FAILED
                await builder_execution_engine._persist_task(task)
                await builder_execution_engine._persist_module(module)
                
        return {"success": True, "mutation_executed": False}

@router.post("/builder/control/{task_id}")
async def control_builder_task(task_id: str, action: str):
    """
    Controls an active builder task (pause, resume, cancel).
    """
    enforce_permission("creator_access")
    task = builder_execution_engine.active_tasks.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if action == "cancel":
        task.status = BuilderStatus.CANCELLED
        return {"status": "success", "message": "Sequence cancelled."}
    
    if action == "retry":
        module_id = task.current_module_id
        if module_id:
            await builder_execution_engine.retry_module(task_id, module_id)
            return {"status": "success", "message": "Retrying module."}
            
    if action == "skip":
        module_id = task.current_module_id
        if module_id:
            await builder_execution_engine.skip_module(task_id, module_id)
            return {"status": "success", "message": "Module skipped."}
    
    return {"status": "error", "message": "Action not implemented or missing target."}
