from fastapi import APIRouter
from .onboarding_manager import onboarding_manager

router = APIRouter()

@router.post("/greeting")
async def process_greeting(data: dict):
    res = await onboarding_manager.process_initial_greeting(
        user_id=data.get("user_id", "new_user"),
        text=data.get("text"),
        browser_lang=data.get("browser_lang", "en")
    )
    return {"status": "ok", "payload": res}
