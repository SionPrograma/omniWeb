from fastapi import APIRouter, Depends, HTTPException
from typing import List, Optional, Dict, Any
from .models import MasterLogbookEntry, MasterLogbookFilter, EntryStatus
from .manager import master_logbook_manager
from backend.core.auth import get_current_user, OmniUser

router = APIRouter()

@router.get("/snapshot", response_model=Dict[str, Any])
async def get_snapshot(current_user: OmniUser = Depends(get_current_user)):
    return master_logbook_manager.get_system_snapshot()

@router.get("/", response_model=List[MasterLogbookEntry])
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
    return master_logbook_manager.get_entries(filters, limit)

@router.post("/", response_model=dict)
async def create_entry(entry: MasterLogbookEntry, current_user: OmniUser = Depends(get_current_user)):
    success = master_logbook_manager.add_entry(entry)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to create entry")
    return {"status": "success", "id": entry.id}

@router.patch("/{entry_id}/status", response_model=dict)
async def update_status(entry_id: str, status: EntryStatus, current_user: OmniUser = Depends(get_current_user)):
    success = master_logbook_manager.update_entry_status(entry_id, status)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to update status")
    return {"status": "success"}
