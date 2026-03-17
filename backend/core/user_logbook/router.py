from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from backend.core.auth import get_current_user, OmniUser
from .models import UserLogbookEntry, UserEntryType, LogbookSearch
from .manager import logbook_manager

router = APIRouter()

@router.post("/create", response_model=UserLogbookEntry)
async def create_entry(
    entry_type: UserEntryType,
    content: str,
    metadata: Optional[dict] = {},
    current_user: OmniUser = Depends(get_current_user)
):
    entry = UserLogbookEntry(
        user_id=current_user.id,
        entry_type=entry_type,
        content=content,
        metadata=metadata
    )
    logbook_manager.add_entry(entry)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="logbook_create",
        status="success",
        message="Entrada guardada en tu bitácora personal.",
        payload={"entry": entry.dict()}
    )
    unified = await orchestrator.orchestrate("create logbook entry", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/list", response_model=List[UserLogbookEntry])
async def list_entries(
    type: Optional[UserEntryType] = None,
    limit: int = 50,
    current_user: OmniUser = Depends(get_current_user)
):
    entries = logbook_manager.list_entries(current_user.id, type, limit)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="logbook_list",
        status="success",
        message=f"He recuperado {len(entries)} entradas de tu bitácora.",
        payload={"entries": [e.dict() for e in entries]}
    )
    unified = await orchestrator.orchestrate("list logbook entries", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/search", response_model=List[UserLogbookEntry])
async def search_entries(
    q: str = Query(..., min_length=1),
    current_user: OmniUser = Depends(get_current_user)
):
    entries = logbook_manager.search_entries(current_user.id, q)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="logbook_search",
        status="success",
        message=f"Búsqueda completada para '{q}'. {len(entries)} resultados encontrados.",
        payload={"entries": [e.dict() for e in entries]}
    )
    unified = await orchestrator.orchestrate(f"search logbook {q}", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
