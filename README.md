# OmniWeb
**Version:** 0.2.0

OmniWeb is a modular personal platform designed to centralize and integrate multiple services, applications, and artificial intelligence instances under a single, unified ecosystem.

## 🏗 Architecture (v0.2.0)
The platform operates as a modular **Multi-Page Application (MPA)** orchestrated by FastAPI, utilizing Vanilla JS for minimal-dependency frontend isolation.

To avoid structural ambiguities, the repository conventions are strict:

- `backend/`: The main Python server (`main.py`) powered by FastAPI.
  - `backend/core/`: **Backend Core**. Python configurations, module registry, and event bus.
- `core/` (root): **Frontend Core**. Vanilla JS logic (`navigation/`, `state/`, `storage/`) shared across all visual applications.
- `frontend/`: Single entrypoint dashboard (served at `/`) linking to active chips. This is **not** a global SPA folder.
- `chips/`: The modern standard for OmniWeb applications. Each chip (`chip-finanzas`, `chip-reparto`, etc.) is an isolated full-stack module (with its own `frontend/` directory and future `api` routes).
- `modules/`: Legacy backend controllers (`lingua`, `planner`, etc.). Currently pending migration to the `chips/` standard.
- `shared/`: Common utility libraries shared between Python backend or general context.
- `docs/`: Official documentation, Architectural Decision Records (ADRs), and sprint logs.
- `scripts/`: Utilities for DevOps.

> **Note:** For deep architectural decisions, check `docs/fase08_arquitectura_v0.2.0.md`.

## 🚀 Vision
This repository formalizes the foundation of the OmniWeb architecture. It transitions legacy isolated projects into a powerful, interconnected digital ecosystem without relying on SPA bloat.
