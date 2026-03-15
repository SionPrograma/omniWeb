# Open Source Module Strategy

## Overview

OmniWeb's modular architecture enables **satellite repository extraction** — individual subsystems that can function independently as open-source packages. This strategy maximizes community contribution while maintaining the integrity of the core platform.

## Proposed Modules

### 1. omniweb-ai-host

**Description**: Multi-processor AI command routing engine with natural language understanding.

| Attribute | Detail |
|---|---|
| Source Path | `backend/core/ai_host/` |
| Dependencies | pydantic, logging |
| Extraction Complexity | Medium |
| Standalone Value | High |

**Key Components**:
- Intent classifier with multilingual support
- Processor registry (plug-and-play command handlers)
- Multimodal input router
- Antimodal response adaptation
- 18 specialized processors

**Use Cases**: Chatbots, command-line AI assistants, voice interface engines

---

### 2. omniweb-storage-grid

**Description**: Fragmented, replicated distributed storage system with integrity verification.

| Attribute | Detail |
|---|---|
| Source Path | `backend/core/storage_grid/` |
| Dependencies | hashlib, sqlite3 |
| Extraction Complexity | Low |
| Standalone Value | High |

**Key Components**:
- Block manager with SHA-256 checksums
- Replication engine with configurable policies
- Integrity sweep with auto-repair
- Shard index service

**Use Cases**: Distributed file storage, censorship-resistant archival, backup systems

---

### 3. omniweb-mesh-network

**Description**: Zero-configuration peer discovery and gossip-based state propagation.

| Attribute | Detail |
|---|---|
| Source Path | `backend/core/distributed_network/`, `infrastructure/` |
| Dependencies | asyncio, aiohttp |
| Extraction Complexity | Medium |
| Standalone Value | High |

**Key Components**:
- Peer discovery without central DNS
- Epidemic gossip protocol
- NAT traversal scaffolding
- Heartbeat monitoring

**Use Cases**: P2P applications, IoT mesh networks, decentralized services

---

### 4. omniweb-knowledge-graph

**Description**: Semantic knowledge graph with type-safe edges and traversal algorithms.

| Attribute | Detail |
|---|---|
| Source Path | `backend/core/knowledge_graph/` |
| Dependencies | pydantic, sqlite3 |
| Extraction Complexity | Low |
| Standalone Value | High |

**Key Components**:
- Knowledge Unit model with type classification
- Relationship edge types (prerequisite, builds_on, contradicts)
- AI-guided traversal recommendations
- Semantic search integration

**Use Cases**: Education platforms, research tools, documentation systems

---

### 5. omniweb-permission-engine

**Description**: Role-based access control with chip-level permissions and creator override.

| Attribute | Detail |
|---|---|
| Source Path | `backend/core/permissions.py`, `backend/core/auth.py` |
| Dependencies | jwt, pydantic |
| Extraction Complexity | Low |
| Standalone Value | Medium |

**Key Components**:
- Role hierarchy (User → Beta → Candidate → Admin → Creator)
- Chip-scoped permission checks
- Operation-level access control
- Creator override mechanism

**Use Cases**: SaaS platforms, multi-tenant applications, API gateways

---

### 6. omniweb-qr-access-kit

**Description**: QR code-based role assignment and PWA installation system.

| Attribute | Detail |
|---|---|
| Source Path | `deployment/qr_access/` |
| Dependencies | qrcode, pillow |
| Extraction Complexity | Very Low |
| Standalone Value | Medium |

**Key Components**:
- QR code generator with embedded role tokens
- Role-based URL construction
- Installation guides per role
- Distribution README templates

**Use Cases**: Event access, beta testing programs, tiered access applications

---

### 7. omniweb-accessibility-layer

**Description**: Multi-modal accessibility integration for inclusive platform access.

| Attribute | Detail |
|---|---|
| Source Path | `backend/core/accessibility/`, `frontend/shell/` |
| Dependencies | None (frontend-based) |
| Extraction Complexity | Medium |
| Standalone Value | Medium |

**Key Components**:
- Voice navigation scaffolding
- Text-based command interface
- Subtitle generation for translations
- Braille output scaffolding
- Cognitive simplification modes

**Use Cases**: Accessibility compliance, inclusive design, assistive technology

---

### 8. omniweb-communication-layer

**Description**: Natural language messaging/calling with auto-translation and contact graph.

| Attribute | Detail |
|---|---|
| Source Path | `backend/core/communication/` |
| Dependencies | pydantic, sqlite3 |
| Extraction Complexity | Low |
| Standalone Value | High |

**Key Components**:
- Natural language intent parsing (ES/EN)
- Contact resolution (name, nickname, relationship)
- Translation adapter with Language Bridge integration
- Conversation memory with persistent logging
- Call session management

**Use Cases**: Multi-language chat apps, CRM systems, customer support platforms

---

## Extraction Feasibility Matrix

| Module | Lines of Code | External Dependencies | Database Tables | Extraction Ready |
|---|---|---|---|---|
| omniweb-ai-host | ~2,000 | pydantic | 0 (stateless) | ⚠️ Needs interface abstraction |
| omniweb-storage-grid | ~500 | hashlib | 2-3 | ✅ Ready |
| omniweb-mesh-network | ~400 | asyncio, aiohttp | 1 | ✅ Ready |
| omniweb-knowledge-graph | ~600 | pydantic | 3-4 | ✅ Ready |
| omniweb-permission-engine | ~300 | jwt | 1 | ✅ Ready |
| omniweb-qr-access-kit | ~100 | qrcode, pillow | 0 | ✅ Ready |
| omniweb-accessibility-layer | ~400 | None | 0 | ⚠️ Frontend coupling |
| omniweb-communication-layer | ~900 | pydantic | 3 | ✅ Ready |

## Recommended Extraction Order

1. **omniweb-qr-access-kit** — Simplest, highest demo appeal
2. **omniweb-knowledge-graph** — Clean API, standalone database
3. **omniweb-storage-grid** — Independent data layer
4. **omniweb-communication-layer** — Complete standalone module
5. **omniweb-permission-engine** — Universal applicability
6. **omniweb-mesh-network** — Infrastructure category
7. **omniweb-ai-host** — Requires processor interface abstraction
8. **omniweb-accessibility-layer** — Requires frontend decoupling

## Repository Structure Template

```
omniweb-{module}/
├── README.md              # Module-specific documentation
├── LICENSE                # MIT License
├── setup.py / pyproject.toml
├── src/
│   └── omniweb_{module}/
│       ├── __init__.py
│       ├── core/          # Business logic
│       └── models/        # Data models
├── tests/
│   └── test_{module}.py
├── examples/
│   └── basic_usage.py
└── docs/
    └── api_reference.md
```
