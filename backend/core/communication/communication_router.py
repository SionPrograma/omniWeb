from fastapi import APIRouter, Depends, HTTPException, Request
from typing import Optional
from backend.core.auth import get_current_user, get_admin_user, OmniUser
from backend.core.communication.contacts_manager import contacts_manager
from backend.core.communication.message_intent_engine import message_intent_engine
from backend.core.communication.call_intent_engine import call_intent_engine
from backend.core.communication.conversation_memory import conversation_memory

router = APIRouter()


# ==========================================
# CONTACTS (Phase 2)
# ==========================================

@router.get("/contacts")
async def get_contacts(current_user: OmniUser = Depends(get_current_user)):
    """Returns the user's contact list."""
    contacts = contacts_manager.get_contacts(current_user.id)
    return [c.model_dump() for c in contacts]


@router.post("/contacts")
async def add_contact(request: Request, current_user: OmniUser = Depends(get_current_user)):
    """Adds a new contact."""
    data = await request.json()
    contact = contacts_manager.add_contact(
        owner_id=current_user.id,
        display_name=data.get("display_name", "Unknown"),
        nickname=data.get("nickname"),
        relationship=data.get("relationship"),
        preferred_language=data.get("preferred_language", "es"),
        contact_user_id=data.get("contact_user_id"),
        email=data.get("email"),
        phone=data.get("phone"),
        notes=data.get("notes")
    )
    return contact.model_dump()


@router.put("/contacts/{contact_id}")
async def update_contact(contact_id: str, request: Request, current_user: OmniUser = Depends(get_current_user)):
    """Updates a contact's information."""
    data = await request.json()
    success = contacts_manager.update_contact(contact_id, **data)
    if not success:
        raise HTTPException(status_code=400, detail="No valid fields to update.")
    return {"status": "success", "message": "Contact updated."}


@router.delete("/contacts/{contact_id}")
async def delete_contact(contact_id: str, current_user: OmniUser = Depends(get_current_user)):
    """Deletes a contact."""
    contacts_manager.delete_contact(contact_id, current_user.id)
    return {"status": "success", "message": "Contact deleted."}


@router.get("/contacts/resolve")
async def resolve_contact(query: str, current_user: OmniUser = Depends(get_current_user)):
    """Resolves a contact by name, nickname, or relationship."""
    contact = contacts_manager.resolve_contact(current_user.id, query)
    if not contact:
        raise HTTPException(status_code=404, detail=f"Contact '{query}' not found.")
    return contact.model_dump()


# ==========================================
# MESSAGING (Phase 3)
# ==========================================

@router.post("/message/send")
async def send_natural_message(request: Request, current_user: OmniUser = Depends(get_current_user)):
    """
    Processes a natural language message command.
    Example: 'write to Juan that I will arrive later'
    """
    data = await request.json()
    command = data.get("command", "")
    result = await message_intent_engine.process_message_command(current_user.id, command)
    return result


@router.post("/message/confirm/{message_id}")
async def confirm_message(message_id: str, current_user: OmniUser = Depends(get_current_user)):
    """Confirms and sends a pending message draft."""
    result = await message_intent_engine.confirm_send(current_user.id, message_id)
    return result


# ==========================================
# CALLS (Phase 5)
# ==========================================

@router.post("/call/start")
async def start_call(request: Request, current_user: OmniUser = Depends(get_current_user)):
    """
    Processes a natural language call command.
    Example: 'call Carl'
    """
    data = await request.json()
    command = data.get("command", "")
    result = await call_intent_engine.process_call_command(current_user.id, command)
    return result


@router.post("/call/end/{session_id}")
async def end_call(session_id: str, current_user: OmniUser = Depends(get_current_user)):
    """Ends an active call session."""
    result = await call_intent_engine.end_call(current_user.id, session_id)
    return result


@router.get("/call/active")
async def get_active_calls(current_user: OmniUser = Depends(get_current_user)):
    """Returns all active call sessions."""
    calls = conversation_memory.get_active_calls(current_user.id)
    return [s.model_dump() for s in calls]


# ==========================================
# CONVERSATION HISTORY (Phase 6)
# ==========================================

@router.get("/history/{contact_id}")
async def get_conversation_history(contact_id: str, limit: int = 20, current_user: OmniUser = Depends(get_current_user)):
    """Returns conversation history with a specific contact."""
    history = conversation_memory.get_conversation_history(current_user.id, contact_id, limit)
    return [e.model_dump() for e in history]


@router.get("/recent")
async def get_recent_conversations(current_user: OmniUser = Depends(get_current_user)):
    """Returns recent unique conversations."""
    return conversation_memory.get_recent_conversations(current_user.id)


# ==========================================
# STATS & MONITORING (Phase 9)
# ==========================================

@router.get("/stats")
async def get_communication_stats(current_user: OmniUser = Depends(get_current_user)):
    """Returns communication statistics for the current user."""
    return conversation_memory.get_stats(current_user.id)


@router.get("/monitor")
async def get_communication_monitor(admin_user: dict = Depends(get_admin_user)):
    """
    Admin: Returns system-wide communication metrics.
    Used by Mission Control Communication Panel.
    """
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context

    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            total_messages = conn.execute("SELECT COUNT(*) as cnt FROM communication_messages").fetchone()["cnt"]
            total_contacts = conn.execute("SELECT COUNT(*) as cnt FROM communication_contacts").fetchone()["cnt"]
            total_conversations = conn.execute("SELECT COUNT(*) as cnt FROM communication_conversation_log").fetchone()["cnt"]
            recent_messages = conn.execute(
                "SELECT sender_id, recipient_contact_id, original_language, target_language, status, timestamp FROM communication_messages ORDER BY timestamp DESC LIMIT 10"
            ).fetchall()

    return {
        "total_messages": total_messages,
        "total_contacts": total_contacts,
        "total_conversation_entries": total_conversations,
        "recent_messages": [dict(m) for m in recent_messages]
    }
