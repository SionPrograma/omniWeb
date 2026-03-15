from typing import Dict, Any, Optional
import logging
from .base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)


class CommunicationProcessor(CommandProcessor):
    """
    OMNIWEB AI HOST COMMUNICATION PROCESSOR
    Handles natural language communication commands routed through the AI Host.
    
    Integrates with:
    - MessageIntentEngine (Phase 3)
    - CallIntentEngine (Phase 5)
    - ContactsManager (Phase 2)
    - TranslationAdapter (Phase 4)
    - ConversationMemory (Phase 6)
    """

    TRIGGER_KEYWORDS = [
        # English
        "write to", "send to", "text", "tell", "call", "phone", "ring",
        "message to", "start conversation",
        # Spanish
        "escribe a", "envía a", "manda a", "dile a", "llama a",
        "llamar", "escríbele", "cuéntale", "mensaje a",
        # Confirmation
        "confirm", "confirmar", "send it", "envíalo", "yes send", "sí envía",
        # Contacts
        "add contact", "agregar contacto", "mis contactos", "my contacts",
    ]

    async def can_handle(self, command: str) -> bool:
        """Detects communication intent in the command."""
        cmd = command.lower()
        return any(kw in cmd for kw in self.TRIGGER_KEYWORDS)

    async def process(self, msg: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        user_id = context.get("user_id", "default_user") if context else "default_user"
        msg_lower = msg.lower().strip()

        # --- Route: Contact Management ---
        if any(k in msg_lower for k in ["my contacts", "mis contactos", "contact list", "lista de contactos"]):
            return await self._handle_contact_list(user_id)

        if any(k in msg_lower for k in ["add contact", "agregar contacto", "nuevo contacto", "new contact"]):
            return AICommandResponse(
                intent="communication_add_contact",
                status="success",
                message=(
                    "📇 To add a contact, provide:\n"
                    "- **Name**: Display name\n"
                    "- **Nickname**: Short alias (optional)\n"
                    "- **Relationship**: e.g., brother, colleague (optional)\n"
                    "- **Language**: Preferred language code (e.g., en, es, fr)\n\n"
                    "Or use the API: `POST /api/v1/communication/contacts`"
                ),
                payload={"action": "add_contact_guide"}
            )

        # --- Route: Confirmation ---
        if any(k in msg_lower for k in ["confirm", "confirmar", "send it", "envíalo", "yes send", "sí envía"]):
            return await self._handle_confirmation(user_id)

        # --- Route: Call ---
        if any(k in msg_lower for k in ["call", "phone", "ring", "llama", "llamar"]):
            return await self._handle_call(user_id, msg)

        # --- Route: Message (default for communication) ---
        return await self._handle_message(user_id, msg)

    async def _handle_message(self, user_id: str, msg: str) -> AICommandResponse:
        """Processes a natural language message command."""
        from backend.core.communication.message_intent_engine import message_intent_engine

        result = await message_intent_engine.process_message_command(user_id, msg)

        if result["status"] == "contact_not_found":
            return AICommandResponse(
                intent="communication_contact_not_found",
                status="warning",
                message=f"⚠️ {result['message']}",
                payload=result
            )

        if result["status"] == "need_message":
            return AICommandResponse(
                intent="communication_need_message",
                status="info",
                message=f"📝 {result['message']}",
                payload=result
            )

        if result["status"] == "pending_confirmation":
            return AICommandResponse(
                intent="communication_pending",
                status="success",
                message=result["confirmation_prompt"],
                payload=result
            )

        if result["status"] == "error":
            return AICommandResponse(
                intent="communication_error",
                status="error",
                message=f"❌ {result['message']}",
                payload=result
            )

        return AICommandResponse(
            intent="communication",
            status="success",
            message="Communication command processed.",
            payload=result
        )

    async def _handle_call(self, user_id: str, msg: str) -> AICommandResponse:
        """Processes a natural language call command."""
        from backend.core.communication.call_intent_engine import call_intent_engine

        result = await call_intent_engine.process_call_command(user_id, msg)

        if result["status"] == "contact_not_found":
            return AICommandResponse(
                intent="call_contact_not_found",
                status="warning",
                message=f"⚠️ {result['message']}",
                payload=result
            )

        return AICommandResponse(
            intent="call_session",
            status="success",
            message=result["message"],
            payload=result
        )

    async def _handle_confirmation(self, user_id: str) -> AICommandResponse:
        """Handles message send confirmation."""
        from backend.core.communication.conversation_memory import conversation_memory

        # Find the latest pending draft for this user
        drafts = conversation_memory._drafts.get(user_id, {})
        if not drafts:
            return AICommandResponse(
                intent="communication_no_pending",
                status="info",
                message="📭 No pending messages to confirm.",
                payload={}
            )

        # Get the most recent draft
        latest_draft = list(drafts.values())[-1]
        from backend.core.communication.message_intent_engine import message_intent_engine
        result = await message_intent_engine.confirm_send(user_id, latest_draft.id)

        return AICommandResponse(
            intent="communication_sent",
            status="success",
            message=f"✅ {result['message']}",
            payload=result
        )

    async def _handle_contact_list(self, user_id: str) -> AICommandResponse:
        """Returns the user's contact list."""
        from backend.core.communication.contacts_manager import contacts_manager

        contacts = contacts_manager.get_contacts(user_id)
        if not contacts:
            return AICommandResponse(
                intent="contacts_empty",
                status="info",
                message="📇 Your contact list is empty. Add contacts to start communicating naturally.",
                payload={"contacts": []}
            )

        contact_lines = []
        for c in contacts:
            line = f"• **{c.display_name}**"
            if c.nickname:
                line += f" ({c.nickname})"
            if c.relationship:
                line += f" — {c.relationship}"
            line += f" 🌐 {c.preferred_language}"
            contact_lines.append(line)

        return AICommandResponse(
            intent="contacts_list",
            status="success",
            message=f"📇 **Your Contacts** ({len(contacts)}):\n\n" + "\n".join(contact_lines),
            payload={"contacts": [c.model_dump() for c in contacts]}
        )


communication_processor = CommunicationProcessor()
