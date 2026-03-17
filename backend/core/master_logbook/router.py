from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from .models import MasterLogbookEntry, MasterLogbookFilter, EntryStatus
from .manager import master_logbook_manager
from backend.core.auth import get_current_user, OmniUser

router = APIRouter()

@router.get("/snapshot", response_model=Dict[str, Any])
async def get_snapshot(current_user: OmniUser = Depends(get_current_user)):
    snapshot = master_logbook_manager.get_system_snapshot()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="master_snapshot",
        status="success",
        message="Instantánea global del sistema capturada y procesada.",
        payload=snapshot
    )
    unified = await orchestrator.orchestrate("get master snapshot", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/")
async def get_entries(
    type: Optional[str] = None, 
    priority: Optional[str] = None, 
    status: Optional[str] = None,
    chip: Optional[str] = None,
    limit: int = 50,
    current_user: OmniUser = Depends(get_current_user)
):
    filters = MasterLogbookFilter(
        type=type,
        priority=priority,
        status=status,
        chip_reference=chip
    )
    entries = master_logbook_manager.get_entries(filters, limit)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="master_list_entries",
        status="success",
        message=f"Se han recuperado {len(entries)} eventos del registro maestro.",
        payload={"entries": [e.dict() if hasattr(e, 'dict') else e for e in entries]}
    )
    unified = await orchestrator.orchestrate("list master logbook", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/")
async def create_entry(entry: MasterLogbookEntry, current_user: OmniUser = Depends(get_current_user)):
    success = master_logbook_manager.add_entry(entry)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create entry")
        
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="master_create_entry",
        status="success",
        message=f"Nuevo evento registrado en el Master Logbook con ID {entry.id}.",
        payload={"id": entry.id}
    )
    unified = await orchestrator.orchestrate("create master logbook entry", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.patch("/{entry_id}/status")
async def update_status(entry_id: str, status: EntryStatus, current_user: OmniUser = Depends(get_current_user)):
    success = master_logbook_manager.update_entry_status(entry_id, status)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update status")
        
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="master_update_status",
        status="success",
        message=f"Estado del evento {entry_id} actualizado a {status.value}.",
        payload={"entry_id": entry_id, "new_status": status.value}
    )
    unified = await orchestrator.orchestrate(f"update master entry {entry_id} to {status}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
