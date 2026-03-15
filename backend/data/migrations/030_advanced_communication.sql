-- Migration 030: Advanced Communication Layer
-- Natural Communication System with Contact Graph, Messaging, Calls, and Conversation Memory

-- Communication Contacts (Phase 2: Contact Graph)
CREATE TABLE IF NOT EXISTS communication_contacts (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    contact_user_id TEXT,
    display_name TEXT NOT NULL,
    nickname TEXT,
    relationship TEXT,
    preferred_language TEXT DEFAULT 'es',
    email TEXT,
    phone TEXT,
    notes TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (owner_user_id) REFERENCES users(id)
);

-- Communication Messages (Phase 3: Natural Messaging)
CREATE TABLE IF NOT EXISTS communication_messages (
    id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL,
    recipient_contact_id TEXT NOT NULL,
    original_text TEXT NOT NULL,
    original_language TEXT DEFAULT 'es',
    translated_text TEXT,
    target_language TEXT,
    status TEXT DEFAULT 'draft',
    channel TEXT DEFAULT 'omniweb',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (sender_id) REFERENCES users(id),
    FOREIGN KEY (recipient_contact_id) REFERENCES communication_contacts(id)
);

-- Conversation Log (Phase 6: Conversation Memory)
CREATE TABLE IF NOT EXISTS communication_conversation_log (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    contact_id TEXT NOT NULL,
    direction TEXT DEFAULT 'outgoing',
    content_type TEXT DEFAULT 'message',
    content_preview TEXT,
    language TEXT DEFAULT 'es',
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metadata TEXT DEFAULT '{}',
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (contact_id) REFERENCES communication_contacts(id)
);

-- Indices for performance
CREATE INDEX IF NOT EXISTS idx_comm_contacts_owner ON communication_contacts(owner_user_id);
CREATE INDEX IF NOT EXISTS idx_comm_contacts_nickname ON communication_contacts(nickname);
CREATE INDEX IF NOT EXISTS idx_comm_messages_sender ON communication_messages(sender_id);
CREATE INDEX IF NOT EXISTS idx_comm_messages_recipient ON communication_messages(recipient_contact_id);
CREATE INDEX IF NOT EXISTS idx_comm_convlog_user ON communication_conversation_log(user_id);
CREATE INDEX IF NOT EXISTS idx_comm_convlog_contact ON communication_conversation_log(contact_id);
