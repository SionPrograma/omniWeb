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
    Orchestrates system actions via natural language processing.
    """
    from backend.core.ai_host.command_router import ai_command_router
    from backend.core.ai_host.interface_adapter import adapter
    from backend.core.database import db_manager

    # 1. Context Persistence
    with db_manager.get_connection() as conn:
        row = conn.execute("SELECT value FROM ai_context_memory WHERE key = 'ai_personality'").fetchone()
        personality = row["value"] if row else "default"
        conn.execute("INSERT INTO ai_context_memory (user_id, key, value) VALUES (?, 'last_msg', ?)", (current_user.id, req.message))
        conn.commit()

    # 2. Command Routing
    outcome = await ai_command_router.route(req.message)
    
    # 3. Event Bus Orchestration
    if outcome.status == "success" and "target" in outcome.payload:
        await event_bus.publish("ai_orchestration_command", {
            "source_chip": "ai-host",
            "command": outcome.payload.get("action", "ACTIVATE_CHIP"),
            "target": outcome.payload["target"]
        })

    # 4. Response Adaptation
    response = adapter.format_response(outcome.message, outcome.payload)
    
    return {
        **response,
        "personality": personality,
        "intent": outcome.intent
    }

