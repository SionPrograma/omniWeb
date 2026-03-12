from fastapi import APIRouter, HTTPException
from .logbook_manager import logbook_manager
from .logbook_affinity_engine import affinity_engine
from .logbook_models import EntryType, ConnectionType
from typing import Optional

router = APIRouter()

@router.get("/me")
async def get_my_logbook(user_id: str = "default_user"):
    return logbook_manager.get_or_create_logbook(user_id)

@router.post("/entries")
async def add_logbook_entry(data: dict):
    user_id = data.get("user_id", "default_user")
    entry_type = EntryType(data.get("type", "idea"))
    content = data.get("content")
    tags = data.get("tags", [])
    
    entry = logbook_manager.add_entry(user_id, entry_type, content, tags)
    if not entry:
        raise HTTPException(status_code=400, detail="Failed to add entry")
    return {"status": "success", "entry": entry}

@router.get("/affinity")
async def get_affinity_suggestions(user_id: str = "default_user"):
    return {"status": "ok", "suggestions": affinity_engine.find_suggestions(user_id)}

@router.post("/connect")
async def connect_to_logbook(data: dict):
    user_id = data.get("user_id", "default_user")
    target_owner_id = data.get("target_user_id")
    conn_type = ConnectionType(data.get("type", "conversation"))
    
    if not target_owner_id:
        raise HTTPException(status_code=400, detail="Missing target_user_id")
        
    logbook_manager.connect_logbooks(user_id, target_owner_id, conn_type)
    return {"status": "connected"}
