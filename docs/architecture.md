# OmniWeb System Architecture

## Overview

OmniWeb is a **distributed, AI-orchestrated knowledge platform** built on FastAPI (Python 3.11+) with a SQLite persistence layer, PWA frontend, and a modular chip plugin system.

The system is designed around three fundamental principles:
1. **Offline-First**: Every node operates autonomously, syncing when connectivity returns.
2. **AI-Orchestrated**: The AI Host manages system health, user mentorship, and governance.
3. **Modular Extensibility**: The Chip System allows plug-and-play feature modules.

---

## Layered Architecture

```
┌─────────────────────────────────────────────┐
│              PRESENTATION LAYER             │
│   OmniShell (PWA) · Dashboard · Chip UIs    │
├─────────────────────────────────────────────┤
│                API GATEWAY                   │
│         FastAPI REST (40+ routers)           │
├─────────────────────────────────────────────┤
│            INTELLIGENCE LAYER                │
│  AI Host · Governance · Communication        │
│  Knowledge Graph · Education · Insights      │
├─────────────────────────────────────────────┤
│           INFRASTRUCTURE LAYER               │
│  Cluster · Mesh · Storage Grid · Sync        │
│  Runtime · Event Bus · Stability Loop        │
├─────────────────────────────────────────────┤
│            PERSISTENCE LAYER                 │
│     SQLite · Migration Engine (30 scripts)   │
│     Long-Term Memory · Master Logbook        │
└─────────────────────────────────────────────┘
```

## Core Modules (60+)

### AI & Intelligence
| Module | Path | Purpose |
|---|---|---|
| AI Host | `core/ai_host/` | 17-processor command routing engine |
| Governance | `core/governance/` | Leadership detection, reputation graph |
| Communication | `core/communication/` | Natural language messaging & calls |
| Knowledge Graph | `core/knowledge_graph/` | Semantic concept connections |
| Insight Engine | `core/insight_engine/` | AI-generated platform insights |
| Semantic Layer | `core/semantic_layer/` | Vector embeddings for search |

### Platform Services
| Module | Path | Purpose |
|---|---|---|
| Education Engine | `core/education_engine/` | Adaptive learning & skill trees |
| Skill Engine | `core/skill_engine/` | Competency certification |
| Opportunity Engine | `core/opportunity_engine/` | Skill-to-opportunity matching |
| Collaboration Spaces | `core/collaboration_spaces/` | Real-time project workspaces |
| Knowledge Economy | `core/knowledge_economy/` | Expertise marketplace |
| Idea Cloud | `core/idea_cloud/` | Collaborative ideation |

### Infrastructure
| Module | Path | Purpose |
|---|---|---|
| Cluster Manager | `core/cluster/` | Multi-node orchestration |
| Distributed Bus | `core/distributed_bus/` | Event routing across nodes |
| Mesh Network | `core/distributed_network/` | Peer discovery |
| Sync Engine | `core/sync/` | Device synchronization |
| Stability Loop | `core/stability_loop/` | Self-healing audit cycle |
| System Auditor | `core/system_auditor/` | Automated health probes |

### Security & Identity
| Module | Path | Purpose |
|---|---|---|
| Permissions | `core/permissions.py` | Role-based access control |
| Auth | `core/auth.py` | JWT authentication |
| Identity | `core/identity/` | User identity management |
| Security | `core/security/` | Creator gateway & audit trail |

## API Structure

All endpoints follow the pattern: `GET|POST /api/v1/{domain}/{resource}`

Major domains:
- `/system/` — Health, state, audit, runtime
- `/ai-host/` — AI command interface
- `/governance/` — Leadership & reputation
- `/communication/` — Contacts, messages, calls
- `/education/` — Learning & skill tracking
- `/scaling/` — Beta testing & observability
- `/creator/` — Creator control plane

## Database

- **Engine**: SQLite (portable, zero-config)
- **Migrations**: 30 versioned SQL scripts in `backend/data/migrations/`
- **Schema**: 50+ tables across user management, knowledge, governance, communication
- **Backup**: Built-in backup/restore via admin API

## Chip Plugin System

Chips are modular applications that extend OmniWeb:

```
chips/chip-{name}/
├── chip.json          # Metadata (slug, version, endpoints)
├── core/
│   ├── router.py      # FastAPI router (auto-registered)
│   ├── service.py     # Business logic
│   └── repository.py  # Data access
└── frontend/
    ├── index.html     # UI entry point
    ├── app.js         # Frontend logic
    └── style.css      # Styles
```

Chips are discovered at startup by the `ModuleRegistry` and auto-mounted to the API and static file servers.

## Deployment

OmniWeb supports multiple deployment modes:
1. **Local Development**: `uvicorn backend.main:app --reload`
2. **Standalone Runtime**: `python -m runtime.boot`
3. **PWA Access**: QR code → mobile browser → "Add to Home Screen"
4. **Cluster Mode**: Multiple nodes with mesh discovery
