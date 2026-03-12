from fastapi import APIRouter, Depends, Security
from pydantic import BaseModel
from typing import Dict, Any, Optional
from backend.core.auth import get_current_user, OmniUser
from backend.core.ai_host.command_router import CommandRouter

router = APIRouter()
ai_router = CommandRouter()

class ProcessRequest(BaseModel):
    message: str
    modality: Optional[str] = "text"

@router.post("/process")
async def process_message(request: ProcessRequest, current_user: OmniUser = Depends(get_current_user)):
    """
    Main entry point for AI Host interactions.
    Processes natural language commands and returns adapted responses.
    """
    cmd_res = await ai_router.route(request.message, modality=request.modality)
    
    # Adapt response using InterfaceAdapter if needed
    from backend.core.ai_host.interface_adapter import adapter
    formatted = adapter.format_response(cmd_res.message, cmd_res.payload)
    formatted["intent"] = cmd_res.intent # Add intent to response for frontend logic
    
    return formatted

@router.get("/status")
async def get_host_status():
    """Returns the current status and mode of the AI Host."""
    return {
        "status": "active",
        "identity": "OmniWeb Host",
        "mode": "hybrid"
    }
