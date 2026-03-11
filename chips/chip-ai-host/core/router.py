from fastapi import APIRouter, HTTPException, Security
from pydantic import BaseModel
from backend.core.event_bus import event_bus
from backend.core.permissions import get_current_chip
from backend.core.auth import get_current_user, OmniUser
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

class AIRequest(BaseModel):
    message: str

from backend.core.database import db_manager

@router.post("/process")
async def process_request(req: AIRequest, current_user: OmniUser = Security(get_current_user)):
    """
    Task 12-17: Processes NL, uses Context Memory and performs Orchestration.
    """
    msg = req.message.lower()
    
    # 1. Fetch AI Personality from Context (Task 16)
    with db_manager.get_connection() as conn:
        row = conn.execute("SELECT value FROM ai_context_memory WHERE key = 'ai_personality'").fetchone()
        personality = row["value"] if row else "default"
        
        # Save interaction log in memory context
        conn.execute("INSERT INTO ai_context_memory (user_id, key, value) VALUES ('1', 'last_msg', ?)", (msg,))
        conn.commit()

    actions = []
    response_text = "I've processed your request."

    # 2. Multi-App Workflow (Task 15-17)
    if "prepara mi sesión" in msg or "prepare my session" in msg:
        actions = ["musica", "finanzas"]
        response_text = f"As your {personality} assistant, I'm opening your workspace (Music + Finances)."
    
    elif "abrir" in msg or "open" in msg:
        target = "none"
        if "finanzas" in msg or "finances" in msg: target = "finanzas"
        elif "reparto" in msg or "delivery" in msg: target = "reparto"
        elif "musica" in msg or "music" in msg: target = "musica"
        
        if target != "none":
            actions = [target]
            response_text = f"Opening {target} module."

    # 4. Chip Factory (Strategic Expansion)
    elif "crear chip" in msg or "create chip" in msg:
        from backend.core.chip_factory import chip_factory
        result = await chip_factory.create_from_request(msg)
        if result["status"] == "success":
            response_text = f"Great! I've created the {result['chip']['name']} chip for you. You can activate it from the OS Admin panel."
        else:
            response_text = f"I failed to create the chip: {result['detail']}"

    # 5. Publish to Orchestration Bus
    for chip in actions:
        await event_bus.publish("ai_orchestration_command", {
            "source_chip": "ai-host",
            "command": "ACTIVATE_CHIP",
            "target": chip
        })

    return {
        "status": "success",
        "personality": personality,
        "actions": actions,
        "message": response_text
    }

