from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Dict, Any, Optional
import os
import json
from .patch_preview import patch_preview_engine, PatchPreview
from .mutation_engine import MutationBatch, FileOperation, MutationType
from .builder_engine import builder_execution_engine, BuilderTask, BuilderModule, BuilderStatus
from backend.core.security.dependencies import get_creator_user
from backend.core.auth import OmniUser
from pydantic import BaseModel

router = APIRouter()

ALLOWED_ROOTS = {
    "chips": "chips",
    "backend": "backend",
    "frontend": "frontend",
    "docs": "docs"
}

PROTECTED_FILES = [".env", "omniweb.db", ".git"]

class FileNode(BaseModel):
    name: str
    path: str
    is_dir: bool
    children: Optional[List['FileNode']] = None

FileNode.update_forward_refs()

def get_file_tree(root_path: str, current_depth: int = 0, max_depth: int = 5) -> List[FileNode]:
    if current_depth > max_depth:
        return []
    
    nodes = []
    try:
        items = sorted(os.listdir(root_path))
        for item in items:
            if item in [".git", "__pycache__", ".venv", "node_modules", ".pytest_cache"]:
                continue
                
            full_path = os.path.join(root_path, item)
            is_dir = os.path.isdir(full_path)
            
            node = FileNode(
                name=item,
                path=full_path,
                is_dir=is_dir
            )
            
            if is_dir:
                node.children = get_file_tree(full_path, current_depth + 1, max_depth)
            
            nodes.append(node)
    except Exception:
        pass
    return nodes

@router.get("/files", response_model=List[FileNode])
async def list_files(root: str = "chips", creator: OmniUser = Depends(get_creator_user)):
    """Lists files in the allowed root directories."""
    if root not in ALLOWED_ROOTS:
        raise HTTPException(status_code=400, detail="Invalid root directory scope")
        
    base_path = ALLOWED_ROOTS[root]
    return get_file_tree(base_path)

@router.get("/file/read")
async def read_file(path: str, creator: OmniUser = Depends(get_creator_user)):
    """Reads the content of a file."""
    # Validation
    abs_path = os.path.abspath(path)
    if not any(abs_path.startswith(os.path.abspath(root)) for root in ALLOWED_ROOTS.values()):
        raise HTTPException(status_code=403, detail="Path outside allowed root scope")
        
    if any(p in abs_path for p in PROTECTED_FILES):
        raise HTTPException(status_code=403, detail="File is protected")

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")
        
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        return {"content": content, "path": path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading file: {str(e)}")

@router.post("/file/propose-edit")
async def propose_edit(
    path: str = Body(...),
    content: str = Body(...),
    creator: OmniUser = Depends(get_creator_user)
):
    """
    Creates a patch preview for a manual edit.
    Wraps the edit in a temporary BuilderTask for logging and approval flow.
    """
    abs_path = os.path.abspath(path)
    if not any(abs_path.startswith(os.path.abspath(root)) for root in ALLOWED_ROOTS.values()):
        raise HTTPException(status_code=403, detail="Path outside allowed root scope")

    # Create a batch
    op = FileOperation(
        path=path,
        op_type=MutationType.MODIFY_FILE,
        content=content
    )
    
    # Check if file exists, if not, op_type should be CREATE_FILE
    if not os.path.exists(path):
        op.op_type = MutationType.CREATE_FILE

    # Create a dummy task/module for this edit
    task = BuilderTask(
        roadmap_id="manual_edit",
        title=f"Manual Edit: {os.path.basename(path)}",
        status=BuilderStatus.AWAITING_APPROVAL
    )
    
    module = BuilderModule(
        task_id=task.id,
        title=f"Applying Changes: {os.path.basename(path)}",
        sequence_order=0,
        status=BuilderStatus.AWAITING_APPROVAL,
        module_type=BuilderModuleType.IMPLEMENTATION
    )
    
    verify_module = BuilderModule(
        task_id=task.id,
        title="Post-Edit Verification",
        sequence_order=1,
        status=BuilderStatus.PENDING,
        module_type=BuilderModuleType.VERIFICATION,
        payload={"path": path}
    )
    
    task.modules.append(module)
    task.modules.append(verify_module)
    
    # Persist task/module so the approval endpoint can find them
    await builder_execution_engine._persist_task(task)
    await builder_execution_engine._persist_module(module)
    
    batch = MutationBatch(
        task_id=task.id,
        module_id=module.id,
        operations=[op],
        origin="CreatorEditor"
    )
    
    preview = patch_preview_engine.generate_preview(task.id, module.id, batch)
    
    # Update module result to point to preview
    module.result = {"preview_id": preview.id, "type": "patch_preview"}
    await builder_execution_engine._persist_module(module)

    # 2. ENFORCE COGNITIVE PIPELINE
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    
    raw_res = AICommandResponse(
        intent="patch_preview",
        status="success",
        message="Patch preview generated. Approval required to apply.",
        payload={"preview_id": preview.id, "task_id": task.id}
    )
    
    unified = await orchestrator.orchestrate(
        message=f"edit {path}",
        understanding={"mode": "action_execution", "intent_group": "BUILD_INTENT"},
        context={"user_id": creator.id},
        raw_response=raw_res
    )
    
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/copilot/assist")
async def copilot_assist(
    action: str = Body(...), # "explain", "optimize", "refactor"
    path: str = Body(...),
    code: Optional[str] = Body(None),
    creator: OmniUser = Depends(get_creator_user)
):
    """Provides Copilot assistance for the current file/code selection."""
    from .copilot_engine import copilot_engine
    
    prompt = f"Action: {action}\nFile: {path}\n"
    if code:
        prompt += f"Selected Code:\n```\n{code}\n```"
    else:
        # Read file if no code selected
        try:
            with open(path, "r", encoding="utf-8") as f:
                prompt += f"Full File Content:\n```\n{f.read()}\n```"
        except:
            pass

    # Use copilot to generate a response
    plan = await copilot_engine.generate_plan(f"System Request: {prompt}")
    
    # ENFORCE COGNITIVE PIPELINE
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    
    raw_res = AICommandResponse(
        intent="copilot_assist",
        status="success",
        message=plan.summary or plan.description or "I've analyzed the request.",
        payload={
            "steps": [step.dict() for step in plan.steps],
            "plan_id": plan.id
        }
    )
    
    unified = await orchestrator.orchestrate(
        message=f"copilot {action} on {path}",
        understanding={"mode": "reflective_analysis", "intent_group": "ANALYSIS_INTENT"},
        context={"user_id": creator.id},
        raw_response=raw_res
    )
    
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/reload")
async def manual_reload(
    module_name: str = Body(...),
    creator: OmniUser = Depends(get_creator_user)
):
    """Manually triggers a reload for a module."""
    from .hot_reload import hot_reload_engine
    success = await hot_reload_engine.reload_module(module_name, ["manual_trigger"])
    if not success:
        raise HTTPException(status_code=500, detail=f"Failed to reload module {module_name}")
    return {"status": "success", "module": module_name}
