from .base import CommandProcessor, AICommandResponse
from backend.core.master_logbook.models import MasterLogbookEntry, EntryType, Priority
from backend.core.master_logbook.manager import master_logbook_manager
import logging
import re

logger = logging.getLogger(__name__)

class LogbookProcessor(CommandProcessor):
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg_lower = msg.lower()
        
        # Determine if it's a query or a creation
        query_keywords = ["show", "muestrame", "busca", "ver", "list", "recent", "get", "recientes"]
        # Improved creation check: only if 'log' is a standalone word or at the start of a command
        # and doesn't conflict with 'show logbook'
        is_creation = any(re.search(rf"\b{w}\b", msg_lower[:15]) for w in ["log", "anota", "guarda", "registra"])
        
        is_query = any(w in msg_lower for w in query_keywords) and not is_creation

        if is_query:
            return await self._handle_query(msg_lower)
        else:
            return await self._handle_creation(msg, msg_lower)

    async def _handle_creation(self, msg: str, msg_lower: str) -> AICommandResponse:
        # 1. Detect Entry Type with synonyms
        type_map = {
            EntryType.BUG: ["bug", "error", "fallo", "problema", "issue", "crash"],
            EntryType.IDEA: ["idea", "pensamiento", "pense", "thought", "posibilidad"],
            EntryType.FIX: ["fix", "arreglo", "corregir", "solucion", "patch"],
            EntryType.DECISION: ["decision", "decisión", "acuerdo", "he decidido"],
            EntryType.TASK: ["task", "tarea", "pendiente", "todo", "hacer"],
            EntryType.TEST: ["test", "prueba", "validar", "verificar"],
            EntryType.ARCHITECTURE: ["arquitectura", "estructura", "diseño", "design"],
            EntryType.ROADMAP: ["roadmap", "hoja de ruta", "plan", "futuro"],
            EntryType.NOTE: ["nota", "apunte", "recordatorio", "memo"]
        }
        
        entry_type = EntryType.NOTE
        for etype, keywords in type_map.items():
            if any(w in msg_lower for w in keywords):
                entry_type = etype
                break

        # 2. Detect Priority
        priority = Priority.MEDIUM
        priority_map = {
            Priority.CRITICAL: ["urgente", "critico", "critical", "alta", "inmediato", "high", "ya"],
            Priority.LOW: ["baja", "low", "despues", "luego", "cuando puedas"],
            Priority.MEDIUM: ["media", "normal", "medium"]
        }
        for prio, keywords in priority_map.items():
            if any(w in msg_lower for w in keywords):
                priority = prio
                break

        # 3. Extract Chip Reference
        chip_ref = None
        # Pattern: "en [chip]", "para [chip]", "de [chip]", "chip [chip]"
        chip_match = re.search(r"(?:for|in|en|para|de|chip|sobre el chip)\s+([a-zA-Z0-9_-]+)", msg_lower)
        if chip_match:
            chip_ref = chip_match.group(1).strip()

        # 4. Clean Content (Remove prefixes and noise)
        content = msg
        prefixes = [
            "log this", "guarda esto", "anota esto", "registra", "loguea", "guarda como",
            "save this", "note this", "create a", "crea un", "crea una"
        ]
        
        # Sort prefixes by length to avoid partial matches
        for p in sorted(prefixes, key=len, reverse=True):
            if msg_lower.startswith(p):
                content = msg[len(p):].strip()
                break
        
        # 5. Get current system snapshot for metadata
        metadata = master_logbook_manager.get_system_snapshot()

        entry = MasterLogbookEntry(
            type=entry_type,
            content=content,
            priority=priority,
            chip_reference=chip_ref,
            author_role="creator",
            metadata=metadata
        )
        
        success = master_logbook_manager.add_entry(entry)
        
        if success:
            type_label = entry_type.value.upper()
            from backend.core.interface.visual_interface import visual_interface
            visual = visual_interface.create_visual_payload(
                "logbook-entry",
                {
                    "id": entry.id,
                    "type": entry_type.value,
                    "priority": priority.value,
                    "content": content
                },
                f"Memory: {type_label}"
            )

            return AICommandResponse(
                intent="logbook_entry_created",
                status="success",
                message=f"✅ Memoria del sistema actualizada. He registrado este {type_label} con prioridad {priority.value}.",
                payload={
                    "entry_id": entry.id, 
                    "type": entry_type.value, 
                    "content": content,
                    "priority": priority.value,
                    "chip": chip_ref,
                    "visual": visual
                }
            )
        else:
            return AICommandResponse(
                intent="logbook_entry_failed",
                status="error",
                message="⚠️ No pude sincronizar con el banco de memoria local.",
                payload={}
            )

    async def _handle_query(self, msg_lower: str) -> AICommandResponse:
        from backend.core.master_logbook.models import MasterLogbookFilter
        
        # Determine filters
        filters = MasterLogbookFilter()
        
        if "bug" in msg_lower or "error" in msg_lower: filters.type = EntryType.BUG
        elif "roadmap" in msg_lower: filters.type = EntryType.ROADMAP
        elif "idea" in msg_lower: filters.type = EntryType.IDEA
        elif "task" in msg_lower or "tarea" in msg_lower: filters.type = EntryType.TASK
        
        entries = master_logbook_manager.get_entries(filters=filters, limit=5)
        
        if not entries:
            return AICommandResponse(
                intent="show_logbook",
                status="success",
                message="No encontré entradas que coincidan con tu búsqueda.",
                payload={"count": 0}
            )
        
        summary = "\n".join([f"- [{e.type.value}] {e.content} ({e.timestamp.strftime('%Y-%m-%d')})" for e in entries])
        
        from backend.core.interface.visual_interface import visual_interface
        visual = visual_interface.create_visual_payload(
            "logbook-list",
            {"entries": [e.dict() for e in entries]},
            "Master Logbook: Búsqueda"
        )
        
        return AICommandResponse(
            intent="show_logbook",
            status="success",
            message=f"Aquí tienes lo que encontré en el logbook:\n{summary}",
            payload={
                "count": len(entries),
                "entries": [e.id for e in entries],
                "visual": visual
            }
        )
