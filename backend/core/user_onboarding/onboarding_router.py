from fastapi import APIRouter
from .onboarding_manager import onboarding_manager

router = APIRouter()

@router.post("/greeting")
async def process_greeting(data: dict):
    res = await onboarding_manager.process_initial_greeting(
        data.get("user_id", "new_user"),
        data.get("text", "")
    )
    return {"status": "ok", "payload": res}
