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
    return entry

@router.get("/list", response_model=List[UserLogbookEntry])
async def list_entries(
    type: Optional[UserEntryType] = None,
    limit: int = 50,
    current_user: OmniUser = Depends(get_current_user)
):
    return logbook_manager.list_entries(current_user.id, type, limit)

@router.get("/search", response_model=List[UserLogbookEntry])
async def search_entries(
    q: str = Query(..., min_length=1),
    current_user: OmniUser = Depends(get_current_user)
):
    return logbook_manager.search_entries(current_user.id, q)
