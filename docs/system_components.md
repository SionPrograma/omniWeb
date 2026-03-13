# System Components Directory

A professional breakdown of the OmniWeb repository structure and component responsibilities.

## Directory Structure

### `/backend`
The Python Kernel. Built with FastAPI for high performance.
- `core/`: Critical system managers (Permissions, Registry, Database).
- `core/ai_host/`: Intelligent command routing engine.
- `core/system_auditor/`: Health monitoring and issue detection.
- `core/security/`: Device trust and creator protection.
- `core/user_logbook/` & `core/user_graph/`: Personal memory and semantic layers.

### `/chips`
The modular application ecosystem.
- Each `chip-{name}` contains its own `chip.json`, `/frontend`, and `/backend`.

### `/frontend`
Global interface resources.
- `shell/`: The PWA host. Manages Navigation, AI UI, and Mission Control.
- `shared/`: Common CSS variables, typography, and utility scripts.

### `/docs`
System documentation, including Architecture Decision Records (ADRs) and User Guides.

### `/user_workspace`
User-specific data silos. Contains SQLite databases and logs for each authenticated user.

## Component Responsibilities

| Component | Responsibility | Technology |
| :--- | :--- | :--- |
| **OmniShell** | Navigation, PWA capability, UI Cohesion | HTML/CSS/JS (Vanilla) |
| **System State Engine** | Real-time health aggregation | Python / React-like State |
| **Galaxy Map** | Visual representation of the node network | CSS 3D / SVGs |
| **AutoFix Engine** | Self-healing and code patching | Python / Unified State |
| **Identity Layer** | Auth and session management | OAuth 2.0 / JWT |
| **Insight Engine** | Pattern detection in user logs | Python / Semantic Graph |
