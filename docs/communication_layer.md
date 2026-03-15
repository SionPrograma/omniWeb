# Communication Layer

## Overview

The **Natural Communication Layer** enables OmniWeb users to send messages and initiate calls using natural language commands. It integrates automatic cross-language translation, contact graph resolution, and conversation memory.

## Architecture

```
┌──────────────────────────────────────────────────────┐
│            COMMUNICATION LAYER                        │
├──────────────────────────────────────────────────────┤
│                                                      │
│  User Speech / Text                                  │
│       │                                              │
│       ▼                                              │
│  ┌──────────────────┐                                │
│  │ Intent Detection │  (Message or Call?)             │
│  └────────┬─────────┘                                │
│           │                                          │
│     ┌─────┴──────┐                                   │
│     ▼            ▼                                   │
│  ┌────────┐  ┌────────┐                              │
│  │Message │  │ Call   │                              │
│  │Intent  │  │Intent  │                              │
│  │Engine  │  │Engine  │                              │
│  └───┬────┘  └───┬────┘                              │
│      │           │                                   │
│      ▼           ▼                                   │
│  ┌──────────────────┐                                │
│  │ Contact Resolution│  (Name/Nickname/Relationship) │
│  └────────┬─────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌──────────────────┐                                │
│  │ Translation      │  (Auto-translate if needed)    │
│  │ Adapter          │                                │
│  └────────┬─────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌──────────────────┐                                │
│  │ User Confirmation│  (Preview before sending)      │
│  └────────┬─────────┘                                │
│           │                                          │
│           ▼                                          │
│  ┌──────────────────┐                                │
│  │ Conversation     │  (Persistent log)              │
│  │ Memory           │                                │
│  └──────────────────┘                                │
└──────────────────────────────────────────────────────┘
```

## Natural Language Commands

### Messaging (English)
| Command | Recipient | Message |
|---|---|---|
| `"write to Juan that I will arrive later"` | Juan | I will arrive later |
| `"tell my brother I am on my way"` | (relationship: brother) | I am on my way |
| `"send a message to Carl"` | Carl | *(prompts for content)* |

### Messaging (Spanish)
| Command | Recipient | Message |
|---|---|---|
| `"escribe a Juan que llegaré tarde"` | Juan | llegaré tarde |
| `"dile a mi hermano que estoy en camino"` | (relationship: hermano) | estoy en camino |
| `"envía un mensaje a Carl"` | Carl | *(prompts for content)* |

### Calls
| Command | Action |
|---|---|
| `"call Carl"` | Initiates call session |
| `"llama a Juan"` | Initiates call session |
| `"start conversation with my brother"` | Initiates call session |

## Contact Graph

Each contact stores:
- **Display Name** — Formal name
- **Nickname** — Short alias for quick resolution
- **Relationship** — Contextual label (brother, colleague, friend)
- **Preferred Language** — For automatic translation
- **Contact User ID** — If they are an OmniWeb user (enables in-app calls)

### Resolution Priority
1. Exact nickname match
2. Exact display name match
3. Relationship match (strips "my"/"mi" prefix)
4. Partial display name match (fuzzy)

## Automatic Translation

When sender and recipient speak different languages:

```
User (Spanish) → "llegaré tarde"
Contact preferred_language = "en"
                    │
                    ▼
Translation Adapter → "I will arrive late"
                    │
                    ▼
Message sent in English
```

Translation sources (in priority order):
1. Local phrase dictionary (~20 common phrases)
2. Language Bridge `TranslationEngine`
3. Fallback: `[LANG] original text`

## Conversation Memory

Tracks per user:
- **Pending Drafts** — Messages awaiting confirmation (in-memory)
- **Sent Messages** — Persistent record with translation data
- **Conversation Log** — Unified timeline (messages + calls)
- **Active Calls** — Currently open call sessions

## Accessibility (Phase 7)

- All commands work via **text** — no mouse required
- Compatible with **voice navigation** accessibility layer
- Translation provides **text subtitles** for cross-language
- Output can be piped to **braille** scaffolding

## Security (Phase 8)

- Authenticated endpoints (JWT)
- Contact ownership enforcement — users only access own contacts
- Message confirmation before sending
- Admin moderation override
- Communication monitor for platform oversight

## Module Files

| File | Lines | Purpose |
|---|---|---|
| `models.py` | 82 | Contact, Message, CallSession, ConversationEntry |
| `contacts_manager.py` | 150 | Contact CRUD + natural language resolution |
| `message_intent_engine.py` | 175 | NL message parsing pipeline |
| `call_intent_engine.py` | 130 | NL call intent parsing |
| `conversation_memory.py` | 170 | Persistent conversation log |
| `translation_adapter.py` | 110 | Language Bridge adapter |
| `communication_router.py` | 160 | FastAPI endpoints |

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/communication/contacts` | List contacts |
| POST | `/api/v1/communication/contacts` | Add contact |
| PUT | `/api/v1/communication/contacts/{id}` | Update contact |
| DELETE | `/api/v1/communication/contacts/{id}` | Delete contact |
| GET | `/api/v1/communication/contacts/resolve?query=` | Resolve contact |
| POST | `/api/v1/communication/message/send` | Natural message |
| POST | `/api/v1/communication/message/confirm/{id}` | Confirm draft |
| POST | `/api/v1/communication/call/start` | Initiate call |
| POST | `/api/v1/communication/call/end/{id}` | End call |
| GET | `/api/v1/communication/call/active` | Active calls |
| GET | `/api/v1/communication/history/{contact_id}` | History |
| GET | `/api/v1/communication/recent` | Recent conversations |
| GET | `/api/v1/communication/stats` | User stats |
| GET | `/api/v1/communication/monitor` | Admin monitor |
