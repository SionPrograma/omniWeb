import json
import uuid
import logging
from typing import List, Optional, Dict
from datetime import datetime
from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from .models import Contact

logger = logging.getLogger(__name__)


class ContactsManager:
    """
    OMNIWEB CONTACT GRAPH (Phase 2)
    Manages the contact layer over the user system.
    Supports nickname mapping, relationship context, and preferred language.
    """

    def add_contact(self, owner_id: str, display_name: str, nickname: str = None,
                    relationship: str = None, preferred_language: str = "es",
                    contact_user_id: str = None, email: str = None,
                    phone: str = None, notes: str = None) -> Contact:
        """Adds a new contact for a user."""
        contact = Contact(
            id=str(uuid.uuid4()),
            owner_user_id=owner_id,
            contact_user_id=contact_user_id,
            display_name=display_name,
            nickname=nickname,
            relationship=relationship,
            preferred_language=preferred_language,
            email=email,
            phone=phone,
            notes=notes,
            created_at=datetime.now()
        )

        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute("""
                    INSERT INTO communication_contacts 
                    (id, owner_user_id, contact_user_id, display_name, nickname, relationship, 
                     preferred_language, email, phone, notes, created_at, metadata)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    contact.id, contact.owner_user_id, contact.contact_user_id,
                    contact.display_name, contact.nickname, contact.relationship,
                    contact.preferred_language, contact.email, contact.phone,
                    contact.notes, contact.created_at.isoformat(), "{}"
                ))
                conn.commit()

        logger.info(f"Contact added: {display_name} for user {owner_id}")
        return contact

    def resolve_contact(self, owner_id: str, query: str) -> Optional[Contact]:
        """
        Resolves a contact by display_name, nickname, or relationship.
        Supports natural language lookups like 'my brother' or 'Carl'.
        """
        query_lower = query.lower().strip()

        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                # Try exact match on nickname first
                row = conn.execute(
                    "SELECT * FROM communication_contacts WHERE owner_user_id = ? AND LOWER(nickname) = ?",
                    (owner_id, query_lower)
                ).fetchone()

                if not row:
                    # Try display_name
                    row = conn.execute(
                        "SELECT * FROM communication_contacts WHERE owner_user_id = ? AND LOWER(display_name) = ?",
                        (owner_id, query_lower)
                    ).fetchone()

                if not row:
                    # Try relationship (e.g., "my brother" -> "brother")
                    clean_query = query_lower.replace("my ", "").replace("mi ", "")
                    row = conn.execute(
                        "SELECT * FROM communication_contacts WHERE owner_user_id = ? AND LOWER(relationship) = ?",
                        (owner_id, clean_query)
                    ).fetchone()

                if not row:
                    # Fuzzy: partial match on display_name
                    row = conn.execute(
                        "SELECT * FROM communication_contacts WHERE owner_user_id = ? AND LOWER(display_name) LIKE ?",
                        (owner_id, f"%{query_lower}%")
                    ).fetchone()

                if row:
                    return self._row_to_contact(row)
        return None

    def get_contacts(self, owner_id: str) -> List[Contact]:
        """Returns all contacts for a user."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                rows = conn.execute(
                    "SELECT * FROM communication_contacts WHERE owner_user_id = ? ORDER BY display_name",
                    (owner_id,)
                ).fetchall()
                return [self._row_to_contact(r) for r in rows]

    def update_contact(self, contact_id: str, **kwargs) -> bool:
        """Updates a contact's fields."""
        allowed = {"display_name", "nickname", "relationship", "preferred_language", "email", "phone", "notes"}
        updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
        if not updates:
            return False

        set_clause = ", ".join(f"{k} = ?" for k in updates.keys())
        values = list(updates.values()) + [contact_id]

        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(f"UPDATE communication_contacts SET {set_clause} WHERE id = ?", values)
                conn.commit()
        return True

    def delete_contact(self, contact_id: str, owner_id: str) -> bool:
        """Deletes a contact."""
        with set_chip_context("core"):
            with db_manager.get_connection() as conn:
                conn.execute(
                    "DELETE FROM communication_contacts WHERE id = ? AND owner_user_id = ?",
                    (contact_id, owner_id)
                )
                conn.commit()
        return True

    def _row_to_contact(self, row) -> Contact:
        return Contact(
            id=row["id"],
            owner_user_id=row["owner_user_id"],
            contact_user_id=row["contact_user_id"],
            display_name=row["display_name"],
            nickname=row["nickname"],
            relationship=row["relationship"],
            preferred_language=row["preferred_language"] or "es",
            email=row["email"],
            phone=row["phone"],
            notes=row["notes"],
            created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else datetime.now(),
            metadata=json.loads(row["metadata"]) if row["metadata"] else {}
        )


contacts_manager = ContactsManager()
