import json
import uuid
import logging
from typing import List, Optional, Dict
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .models import Message, MessageStatus, CallSession, CallStatus, ConversationEntry

logger = logging.getLogger(__name__)


class ConversationMemory:
    """
    OMNIWEB CONVERSATION MEMORY (Phase 6)
    Contextual conversation memory tracking:
    - Last messages per contact
    - Language preferences per conversation
    - Conversation patterns
    - Pending drafts and active call sessions
    """

    def __init__(self):
        # In-memory draft cache (ephemeral until sent)
        self._drafts: Dict[str, Dict[str, Message]] = {}   # {user_id: {msg_id: Message}}
        self._call_sessions: Dict[str, Dict[str, CallSession]] = {}  # {user_id: {session_id: CallSession}}

    # --- Message Drafts ---

    def store_draft(self, user_id: str, message: Message):
        """Caches a message draft pending user confirmation."""
        if user_id not in self._drafts:
            self._drafts[user_id] = {}
        self._drafts[user_id][message.id] = message

    def get_draft(self, user_id: str, message_id: str) -> Optional[Message]:
        """Retrieves a pending draft."""
        return self._drafts.get(user_id, {}).get(message_id)

    def clear_draft(self, user_id: str, message_id: str):
        """Removes a draft after sending or cancellation."""
        if user_id in self._drafts:
            self._drafts[user_id].pop(message_id, None)

    # --- Sent Messages (Persistent) ---

    def record_sent_message(self, user_id: str, message: Message):
        """Records a sent message to the database."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO communication_messages 
                    (id, sender_id, recipient_contact_id, original_text, original_language,
                     translated_text, target_language, status, channel, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    message.id, message.sender_id, message.recipient_contact_id,
                    message.original_text, message.original_language,
                    message.translated_text, message.target_language,
                    message.status.value, message.channel,
                    message.timestamp.isoformat(), json.dumps(message.metadata)
                ))

                # Also record as conversation entry
                conn.execute("""
                    INSERT INTO communication_conversation_log 
                    (id, user_id, contact_id, direction, content_type, content_preview, language, timestamp, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(uuid.uuid4()), user_id, message.recipient_contact_id,
                    "outgoing", "message", message.original_text[:100],
                    message.original_language, datetime.now().isoformat(), "{}"
                ))
                conn.commit()

        # Clear draft
        self.clear_draft(user_id, message.id)
        logger.info(f"Message {message.id} sent and recorded.")

    def get_conversation_history(self, user_id: str, contact_id: str, limit: int = 20) -> List[ConversationEntry]:
        """Retrieves the conversation history with a specific contact."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("""
                    SELECT * FROM communication_conversation_log 
                    WHERE user_id = ? AND contact_id = ?
                    ORDER BY timestamp DESC LIMIT ?
                """, (user_id, contact_id, limit)).fetchall()
                return [ConversationEntry(
                    id=r["id"],
                    user_id=r["user_id"],
                    contact_id=r["contact_id"],
                    direction=r["direction"],
                    content_type=r["content_type"],
                    content_preview=r["content_preview"],
                    language=r["language"],
                    timestamp=datetime.fromisoformat(r["timestamp"]),
                    metadata=json.loads(r["metadata"]) if r["metadata"] else {}
                ) for r in rows]

    def get_recent_conversations(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Returns recent unique conversations for a user."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute("""
                    SELECT contact_id, MAX(timestamp) as last_time, content_preview, direction
                    FROM communication_conversation_log 
                    WHERE user_id = ?
                    GROUP BY contact_id
                    ORDER BY last_time DESC
                    LIMIT ?
                """, (user_id, limit)).fetchall()
                return [dict(r) for r in rows]

    # --- Call Sessions ---

    def store_call_session(self, user_id: str, session: CallSession):
        """Stores a call session."""
        if user_id not in self._call_sessions:
            self._call_sessions[user_id] = {}
        self._call_sessions[user_id][session.id] = session

    def get_call_session(self, user_id: str, session_id: str) -> Optional[CallSession]:
        return self._call_sessions.get(user_id, {}).get(session_id)

    def update_call_session(self, user_id: str, session: CallSession):
        """Persists a call session record to the database."""
        if user_id in self._call_sessions:
            self._call_sessions[user_id][session.id] = session

        # Persist ended calls
        if session.status in (CallStatus.ENDED, CallStatus.MISSED, CallStatus.FAILED):
            with set_chip_context("core"):
                with db_manager.get_connection() as conn:
                    conn.execute("""
                        INSERT INTO communication_conversation_log 
                        (id, user_id, contact_id, direction, content_type, content_preview, language, timestamp, metadata)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        str(uuid.uuid4()), user_id, session.callee_contact_id,
                        "outgoing", "call",
                        f"Call ({session.status.value}) - {session.duration_seconds}s",
                        "es", datetime.now().isoformat(),
                        json.dumps({"session_id": session.id, "duration": session.duration_seconds})
                    ))
                    conn.commit()

    def get_active_calls(self, user_id: str) -> List[CallSession]:
        """Returns all active/ringing call sessions."""
        sessions = self._call_sessions.get(user_id, {})
        return [s for s in sessions.values() if s.status in (CallStatus.INITIATING, CallStatus.RINGING, CallStatus.ACTIVE)]

    # --- Communication Stats ---

    def get_stats(self, user_id: str) -> Dict:
        """Returns communication statistics for a user."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                msg_count = conn.execute(
                    "SELECT COUNT(*) as cnt FROM communication_messages WHERE sender_id = ?",
                    (user_id,)
                ).fetchone()["cnt"]
                conv_count = conn.execute(
                    "SELECT COUNT(DISTINCT contact_id) as cnt FROM communication_conversation_log WHERE user_id = ?",
                    (user_id,)
                ).fetchone()["cnt"]
                contact_count = conn.execute(
                    "SELECT COUNT(*) as cnt FROM communication_contacts WHERE owner_user_id = ?",
                    (user_id,)
                ).fetchone()["cnt"]
        return {
            "messages_sent": msg_count,
            "unique_conversations": conv_count,
            "total_contacts": contact_count,
            "active_calls": len(self.get_active_calls(user_id))
        }


conversation_memory = ConversationMemory()
