import re
import uuid
import logging
from typing import Optional, Dict, Any
from datetime import datetime
from .models import CallSession, CallStatus
from .contacts_manager import contacts_manager
from .conversation_memory import conversation_memory

logger = logging.getLogger(__name__)


class CallIntentEngine:
    """
    OMNIWEB CALL INTENT ENGINE (Phase 5)
    Parses natural language commands for initiating calls/conversations.
    
    Supported patterns:
      - "call Carl"
      - "start conversation with Juan"
      - "llama a Carl"
      - "inicia conversación con Juan"
    """

    PATTERNS_EN = [
        r"(?:call|phone|ring)\s+(.+)",
        r"(?:start|begin|open)\s+(?:a\s+)?(?:call|conversation|chat)\s+(?:with\s+)?(.+)",
    ]

    PATTERNS_ES = [
        r"(?:llama|llamar|marca)\s+(?:a\s+)?(.+)",
        r"(?:inicia|iniciar|abre|abrir)\s+(?:una\s+)?(?:llamada|conversación|charla)\s+(?:con\s+)?(.+)",
    ]

    def parse_intent(self, raw_command: str) -> Dict[str, Any]:
        """Parses call intent from natural language."""
        command = raw_command.strip()
        result = {
            "intent": "call",
            "recipient_raw": None,
            "parsed": False,
            "raw_command": command
        }

        for pattern in self.PATTERNS_ES:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                result["recipient_raw"] = match.group(1).strip()
                result["parsed"] = True
                return result

        for pattern in self.PATTERNS_EN:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                result["recipient_raw"] = match.group(1).strip()
                result["parsed"] = True
                return result

        return result

    async def process_call_command(self, user_id: str, raw_command: str) -> Dict[str, Any]:
        """
        Full call pipeline:
        User Speech → Intent Detection → Contact Resolution → Session Creation
        """
        # Step 1: Intent Detection
        intent = self.parse_intent(raw_command)
        if not intent["parsed"] or not intent["recipient_raw"]:
            return {
                "status": "error",
                "message": "I couldn't understand who you want to call. Try: 'call [name]'",
                "intent": intent
            }

        # Step 2: Contact Resolution
        contact = contacts_manager.resolve_contact(user_id, intent["recipient_raw"])
        if not contact:
            return {
                "status": "contact_not_found",
                "message": f"I couldn't find '{intent['recipient_raw']}' in your contacts.",
                "intent": intent
            }

        # Step 3: Create Call Session (scaffolding)
        session = CallSession(
            id=str(uuid.uuid4()),
            caller_id=user_id,
            callee_contact_id=contact.id,
            status=CallStatus.INITIATING,
            start_time=datetime.now(),
            translation_active=(contact.preferred_language != "es")
        )

        # Store session
        conversation_memory.store_call_session(user_id, session)

        # Step 4: Check if contact is an OmniWeb user (for in-app call)
        if contact.contact_user_id:
            session.status = CallStatus.RINGING
            return {
                "status": "ringing",
                "message": f"📞 Calling **{contact.display_name}**...",
                "session": {
                    "id": session.id,
                    "callee": contact.display_name,
                    "translation_active": session.translation_active,
                    "target_language": contact.preferred_language
                }
            }
        else:
            # External contact — future integration point
            return {
                "status": "session_created",
                "message": (
                    f"📞 Call session created for **{contact.display_name}**.\n"
                    f"{'🌐 Translation: Active (' + contact.preferred_language + ')' if session.translation_active else ''}\n\n"
                    f"*Voice infrastructure is being provisioned. Session ID: `{session.id[:8]}`*"
                ),
                "session": {
                    "id": session.id,
                    "callee": contact.display_name,
                    "translation_active": session.translation_active,
                    "status": session.status.value
                }
            }

    async def end_call(self, user_id: str, session_id: str) -> Dict[str, Any]:
        """Ends an active call session."""
        session = conversation_memory.get_call_session(user_id, session_id)
        if not session:
            return {"status": "error", "message": "No active call session found."}

        session.status = CallStatus.ENDED
        session.end_time = datetime.now()
        session.duration_seconds = int((session.end_time - session.start_time).total_seconds())

        conversation_memory.update_call_session(user_id, session)

        return {
            "status": "ended",
            "message": f"📞 Call ended. Duration: {session.duration_seconds}s",
            "session_id": session.id
        }


call_intent_engine = CallIntentEngine()
