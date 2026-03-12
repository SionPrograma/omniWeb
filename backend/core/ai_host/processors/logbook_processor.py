from .base import CommandProcessor, AICommandResponse
from backend.core.master_logbook.models import MasterLogbookEntry, EntryType, Priority
from backend.core.master_logbook.manager import master_logbook_manager
import logging
import re

logger = logging.getLogger(__name__)

class LogbookProcessor(CommandProcessor):
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg_lower = msg.lower()
        
        # Simple rule-based extraction for MVP
        entry_type = EntryType.NOTE
        if any(w in msg_lower for w in ["bug", "error", "fallo"]):
            entry_type = EntryType.BUG
        elif any(w in msg_lower for w in ["idea", "pensamiento"]):
            entry_type = EntryType.IDEA
        elif any(w in msg_lower for w in ["fix", "arreglo", "corregir"]):
            entry_type = EntryType.FIX
        elif any(w in msg_lower for w in ["decision", "decisión"]):
            entry_type = EntryType.DECISION
        elif any(w in msg_lower for w in ["task", "tarea", "pendiente"]):
            entry_type = EntryType.TASK
        elif any(w in msg_lower for w in ["test", "prueba"]):
            entry_type = EntryType.TEST

        priority = Priority.MEDIUM
        if any(w in msg_lower for w in ["urgente", "critico", "critical", "alta"]):
            priority = Priority.CRITICAL
        elif any(w in msg_lower for w in ["baja", "low"]):
            priority = Priority.LOW

        # Try to extract chip reference
        chip_ref = None
        chip_match = re.search(r"(?:for|in|en|para|chip)\s+([a-zA-Z0-9_-]+)", msg_lower)
        if chip_match:
            chip_ref = chip_match.group(1)

        content = msg
        prefixes = ["log this", "guarda esto", "anota esto", "registra", "loguea", "guarda como"]
        for p in prefixes:
            if msg_lower.startswith(p):
                content = msg[len(p):].strip()
                break

        entry = MasterLogbookEntry(
            type=entry_type,
            content=content,
            priority=priority,
            chip_reference=chip_ref,
            author_role="creator"
        )
        
        success = master_logbook_manager.add_entry(entry)
        
        if success:
            return AICommandResponse(
                intent="logbook_entry_created",
                status="success",
                message=f"He registrado esta entrada en el Master Logbook como {entry_type.value}.",
                payload={"entry_id": entry.id, "type": entry_type.value, "content": content}
            )
        else:
            return AICommandResponse(
                intent="logbook_entry_failed",
                status="error",
                message="No pude guardar la entrada en el logbook local.",
                payload={}
            )
