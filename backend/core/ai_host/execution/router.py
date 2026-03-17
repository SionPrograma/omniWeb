from fastapi import APIRouter, Security, HTTPException, Depends
from typing import List, Dict, Any
from .copilot_engine import copilot_engine, CopilotActionPlan
from .builder_engine import builder_execution_engine, BuilderTask, BuilderStatus
from backend.core.permissions import enforce_permission, set_chip_context
from backend.core.auth import get_current_user, OmniUser
from backend.core.master_logbook.manager import master_logbook_manager

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
        return plan

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
        return result

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
        
        if action == "retry":
            if task.current_module_id:
                await builder_execution_engine.retry_module(task_id, task.current_module_id)
                return {"success": True, "message": "Module retry initiated"}
        elif action == "cancel":
            task.status = BuilderStatus.CANCELLED
            await builder_execution_engine._persist_task(task)
            return {"success": True, "message": "Task cancelled"}
            
        raise HTTPException(status_code=400, detail=f"Unsupported action: {action}")

@router.post("/builder/preview/{preview_id}/decide")
async def decide_preview(preview_id: str, approved: bool, current_user: OmniUser = Depends(get_current_user)):
    with set_chip_context("ai-host", current_user.id):
        enforce_permission("creator_access")
        from .patch_preview import patch_preview_engine
        from .mutation_engine import mutation_engine
        
        preview = await patch_preview_engine.get_preview(preview_id)
        if not preview:
            raise HTTPException(status_code=404, detail="Preview not found")
        
        if approved:
            # Apply mutation
            results = await mutation_engine.execute_batch(preview.batch)
            
            # Update task/module status
            task = await builder_execution_engine.get_task(preview.task_id)
            if task:
                module = next((m for m in task.modules if m.id == preview.module_id), None)
                if module:
                    module.status = BuilderStatus.COMPLETED
                    module.progress = 100.0
                    module.result = {"success": True, "hot_reload": results}
                    await builder_execution_engine._persist_module(module)
                    
                    # Continue execution loop
                    import asyncio
                    asyncio.create_task(builder_execution_engine._execute_loop(task))
            
            return {"success": True, "message": "Patch applied successfully", "reload_results": results}
        else:
            return {"success": True, "message": "Patch rejected"}
