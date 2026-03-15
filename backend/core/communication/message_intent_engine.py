import re
import uuid
import logging
from typing import Optional, Dict, Any, Tuple
from datetime import datetime
from .models import Message, MessageStatus
from .contacts_manager import contacts_manager
from .translation_adapter import translation_adapter
from .conversation_memory import conversation_memory

logger = logging.getLogger(__name__)


class MessageIntentEngine:
    """
    OMNIWEB NATURAL MESSAGING ENGINE (Phase 3)
    Parses natural language commands to extract messaging intent.
    
    Supported patterns:
      - "write to Juan that I will arrive later"
      - "tell my brother I am on my way"
      - "send this message to Carl"
      - "escribe a Juan que llegaré tarde"
      - "dile a mi hermano que estoy en camino"
    """

    # Intent patterns: (regex, groups: recipient_group, message_group)
    PATTERNS_EN = [
        (r"(?:write|send|text|message)\s+(?:to\s+)?(.+?)\s+(?:that|saying|:)\s+(.+)", 1, 2),
        (r"tell\s+(.+?)\s+(?:that\s+)?(.+)", 1, 2),
        (r"(?:write|send|text)\s+(?:a\s+)?(?:message\s+)?(?:to\s+)?(.+)", 1, None),
    ]

    PATTERNS_ES = [
        (r"(?:escribe|envía|manda|escríbele)\s+(?:a\s+)?(.+?)\s+(?:que|diciendo|:)\s+(.+)", 1, 2),
        (r"(?:dile|dígale|cuéntale)\s+(?:a\s+)?(.+?)\s+(?:que\s+)?(.+)", 1, 2),
        (r"(?:escribe|envía|manda)\s+(?:un\s+)?(?:mensaje\s+)?(?:a\s+)?(.+)", 1, None),
    ]

    def parse_intent(self, raw_command: str) -> Dict[str, Any]:
        """
        Parses a natural language command and extracts:
        - recipient (name/nickname/relationship)
        - message_body (the content to send)
        - language_hint (detected input language)
        """
        command = raw_command.strip()
        result = {
            "intent": "message",
            "recipient_raw": None,
            "message_body": None,
            "language_hint": self._detect_language(command),
            "raw_command": command,
            "parsed": False
        }

        # Try Spanish patterns first
        for pattern, rec_group, msg_group in self.PATTERNS_ES:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                result["recipient_raw"] = match.group(rec_group).strip()
                if msg_group:
                    result["message_body"] = match.group(msg_group).strip()
                result["parsed"] = True
                result["language_hint"] = "es"
                return result

        # Try English patterns
        for pattern, rec_group, msg_group in self.PATTERNS_EN:
            match = re.search(pattern, command, re.IGNORECASE)
            if match:
                result["recipient_raw"] = match.group(rec_group).strip()
                if msg_group:
                    result["message_body"] = match.group(msg_group).strip()
                result["parsed"] = True
                result["language_hint"] = "en"
                return result

        return result

    async def process_message_command(self, user_id: str, raw_command: str) -> Dict[str, Any]:
        """
        Full pipeline:
        User Speech → Intent Detection → Contact Resolution → Message Draft → 
        Language Adaptation → User Confirmation → Send
        """
        # Step 1: Intent Detection
        intent = self.parse_intent(raw_command)
        if not intent["parsed"] or not intent["recipient_raw"]:
            return {
                "status": "error",
                "message": "I couldn't understand who you want to message. Try: 'write to [name] that [message]'",
                "intent": intent
            }

        # Step 2: Contact Resolution
        contact = contacts_manager.resolve_contact(user_id, intent["recipient_raw"])
        if not contact:
            return {
                "status": "contact_not_found",
                "message": f"I couldn't find '{intent['recipient_raw']}' in your contacts. Would you like to add them?",
                "intent": intent
            }

        # Step 3: Message Draft
        message_body = intent["message_body"]
        if not message_body:
            return {
                "status": "need_message",
                "message": f"What would you like to say to {contact.display_name}?",
                "contact": contact.model_dump(),
                "intent": intent
            }

        # Step 4: Language Adaptation (auto-translate if needed)
        original_lang = intent["language_hint"]
        target_lang = contact.preferred_language
        translated_text = None

        if original_lang != target_lang:
            translated_text = await translation_adapter.translate_text(
                message_body, original_lang, target_lang
            )

        # Step 5: Build draft for confirmation
        draft = Message(
            id=str(uuid.uuid4()),
            sender_id=user_id,
            recipient_contact_id=contact.id,
            original_text=message_body,
            original_language=original_lang,
            translated_text=translated_text,
            target_language=target_lang if translated_text else None,
            status=MessageStatus.PENDING_CONFIRMATION
        )

        # Store in conversation memory
        conversation_memory.store_draft(user_id, draft)

        response = {
            "status": "pending_confirmation",
            "contact": {
                "name": contact.display_name,
                "language": contact.preferred_language
            },
            "message": {
                "id": draft.id,
                "original": message_body,
                "translated": translated_text,
                "target_language": target_lang if translated_text else original_lang
            }
        }

        if translated_text:
            response["confirmation_prompt"] = (
                f"📨 **To**: {contact.display_name}\n"
                f"📝 **Original** ({original_lang}): {message_body}\n"
                f"🌐 **Translated** ({target_lang}): {translated_text}\n\n"
                f"Send this message? (confirm / cancel)"
            )
        else:
            response["confirmation_prompt"] = (
                f"📨 **To**: {contact.display_name}\n"
                f"📝 **Message**: {message_body}\n\n"
                f"Send this message? (confirm / cancel)"
            )

        return response

    async def confirm_send(self, user_id: str, message_id: str) -> Dict[str, Any]:
        """Confirms and sends a pending message."""
        draft = conversation_memory.get_draft(user_id, message_id)
        if not draft:
            return {"status": "error", "message": "No pending message found."}

        # Mark as sent
        draft.status = MessageStatus.SENT
        conversation_memory.record_sent_message(user_id, draft)

        return {
            "status": "sent",
            "message": f"✅ Message sent to {draft.recipient_contact_id}.",
            "message_id": draft.id
        }

    def _detect_language(self, text: str) -> str:
        """Quick language detection heuristic."""
        es_indicators = ["que", "qué", "a mi", "dile", "escribe", "envía", "hermano", "llegaré"]
        en_indicators = ["write", "send", "tell", "that", "my", "brother", "message"]
        
        text_lower = text.lower()
        es_score = sum(1 for w in es_indicators if w in text_lower)
        en_score = sum(1 for w in en_indicators if w in text_lower)
        
        return "es" if es_score >= en_score else "en"


message_intent_engine = MessageIntentEngine()
