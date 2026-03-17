from fastapi import APIRouter, HTTPException, Security, Depends
from backend.core.auth import get_admin_user, OmniUser, get_current_user
from backend.core.stability_loop.loop_controller import loop_controller
from backend.core.stability_loop.loop_models import TaskState

router = APIRouter()

@router.get("/status")
async def get_task_status(task_id: str):
    """Returns the current state of a specific stability loop task."""
    status = loop_controller.get_task_status(task_id)
    if not status:
        raise HTTPException(status_code=404, detail="Stability task not found")
        
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="stability_status",
        status="success",
        message=f"Estado de la tarea de estabilidad {task_id} recuperado.",
        payload=status
    )
    unified = await orchestrator.orchestrate(f"stability status {task_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/active")
async def get_active_tasks(admin_user: OmniUser = Security(get_admin_user)):
    tasks = list(loop_controller.active_tasks.values())
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="stability_active",
        status="success",
        message=f"Se encontraron {len(tasks)} tareas de estabilidad activas.",
        payload={"tasks": tasks}
    )
    unified = await orchestrator.orchestrate("active stability tasks", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
