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
    return status

@router.get("/active")
async def get_active_tasks(admin_user: OmniUser = Security(get_admin_user)):
    """Returns all active tasks currently being managed by the loop controller."""
    return list(loop_controller.active_tasks.values())
