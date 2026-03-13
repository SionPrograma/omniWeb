import logging
import re
from typing import Dict, Any, Optional, List
from .base import CommandProcessor, AICommandResponse
from backend.core.user_logbook.models import UserLogbookEntry, UserEntryType
from backend.core.user_logbook.manager import logbook_manager
from backend.core.auth import OmniUser

logger = logging.getLogger(__name__)

class UserLogbookProcessor(CommandProcessor):
    """
    AI Host Processor for User Personal Memory System.
    Phase 17: User Personal Logbook.
    """

    async def can_handle(self, command: str) -> bool:
        terms = ["mi logbook", "mi memoria", "anota para mi", "log idea", "create task", "mis notas", "summary user activity"]
        cmd = command.lower()
        return any(term in cmd for term in terms)

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = command.lower()
        
        # Determine User (default to current if not provided in context)
        # Note: In real flow, the router should pass the user object.
        user_id = str(context.get("user_id", "1")) if context else "1"
        
        # 1. Summarize Activity
        if any(x in cmd for x in ["summary", "resumen", "actividad"]):
            return await self._handle_summary(user_id)
            
        # 2. Query Notes/Tasks
        if any(x in cmd for x in ["show", "list", "ver", "mis"]):
            return await self._handle_list(user_id, cmd)
            
        # 3. Creation
        return await self._handle_creation(user_id, command, cmd)

    async def _handle_creation(self, user_id: str, command: str, cmd_lower: str) -> AICommandResponse:
        # Detect Type
        entry_type = UserEntryType.NOTE
        if any(x in cmd_lower for x in ["idea", "pensamiento"]): entry_type = UserEntryType.IDEA
        elif any(x in cmd_lower for x in ["task", "tarea", "pendiente"]): entry_type = UserEntryType.TASK
        
        # Extract Content (remove common prefixes)
        content = command
        prefixes = ["log idea", "create task", "anota", "guarda", "para mi logbook"]
        for p in prefixes:
            if cmd_lower.startswith(p):
                content = command[len(p):].strip()
                break
        
        entry = UserLogbookEntry(
            user_id=user_id,
            entry_type=entry_type,
            content=content
        )
        
        logbook_manager.add_entry(entry)
        
        return AICommandResponse(
            intent="user_logbook_created",
            status="success",
            message=f"✅ He guardado esta entrada en tu logbook personal como **{entry_type.value}**.",
            payload={"entry": entry.model_dump(mode='json')}
        )

    async def _handle_list(self, user_id: str, cmd_lower: str) -> AICommandResponse:
        etype = None
        if "idea" in cmd_lower: etype = UserEntryType.IDEA
        elif "task" in cmd_lower or "tarea" in cmd_lower: etype = UserEntryType.TASK
        
        entries = logbook_manager.list_entries(user_id, etype, limit=5)
        
        if not entries:
            return AICommandResponse(
                intent="user_logbook_list",
                status="success",
                message="No encontré memorias guardadas en tu logbook personal."
            )
            
        list_text = "\n".join([f"- [{e.entry_type.value}] {e.content}" for e in entries])
        return AICommandResponse(
            intent="user_logbook_list",
            status="success",
            message=f"Esto es lo que encontré en tu memoria personal:\n\n{list_text}",
            payload={"entries": [e.model_dump(mode='json') for e in entries]}
        )

    async def _handle_summary(self, user_id: str) -> AICommandResponse:
        entries = logbook_manager.list_entries(user_id, limit=20)
        
        counts = {t.value: 0 for t in UserEntryType}
        for e in entries:
            counts[e.entry_type.value] += 1
            
        summary = (
            f"### 📔 Resumen de tu Registro Personal\n"
            f"- **Tareas Pendientes**: {counts['task']}\n"
            f"- **Ideas Guardadas**: {counts['idea']}\n"
            f"- **Notas**: {counts['note']}\n"
            f"- **Eventos Recientes**: {counts['system_event'] + counts['chip_event']}\n\n"
            f"¿Quieres que revisemos alguna de tus ideas o tareas pendientes?"
        )
        
        return AICommandResponse(
            intent="user_logbook_summary",
            status="success",
            message=summary,
            payload={"counts": counts}
        )
