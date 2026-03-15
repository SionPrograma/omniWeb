<p align="center">
  <img src="docs/assets/logo_placeholder.svg" alt="OmniWeb Logo" width="120"/>
</p>

<h1 align="center">OmniWeb</h1>

<p align="center">
  <strong>Distributed AI Knowledge Platform</strong><br/>
  <em>A self-healing, mesh-networked ecosystem for human development, knowledge economics, and AI-guided governance.</em>
</p>

<p align="center">
  <img src="https://img.shields.io/badge/version-1.0_beta-blue?style=flat-square" alt="Version"/>
  <img src="https://img.shields.io/badge/python-3.11+-green?style=flat-square" alt="Python"/>
  <img src="https://img.shields.io/badge/framework-FastAPI-009688?style=flat-square" alt="FastAPI"/>
  <img src="https://img.shields.io/badge/database-SQLite-003B57?style=flat-square" alt="SQLite"/>
  <img src="https://img.shields.io/badge/frontend-PWA-FFD700?style=flat-square" alt="PWA"/>
  <img src="https://img.shields.io/badge/license-MIT-orange?style=flat-square" alt="License"/>
</p>

---

## 🌐 What is OmniWeb?

OmniWeb is a **distributed, AI-orchestrated knowledge platform** that transforms the web into a structured engine for human potential. It replaces centralized architecture with a global mesh of autonomous nodes, where every user is a creator, every fragment of knowledge is a permanent artifact, and every skill is a tradable currency.

### Core Pillars

| Pillar | Description |
|---|---|
| 🧠 **AI Host** | Persistent AI orchestrator for system health, user mentorship, and autonomous development |
| 🌍 **Distributed Runtime** | Peer-to-peer execution surviving total disconnection with offline-first architecture |
| 📚 **Digital Alexandria** | Fragmented, redundant storage grid ensuring knowledge is never lost or censored |
| 🏛️ **Governance Engine** | AI-driven leadership detection, reputation graph, and community self-governance |
| 📡 **Communication Layer** | Natural language messaging and calling with automatic cross-language translation |

---

## 🏗️ Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        OmniWeb Architecture                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────────┐  │
│  │  OmniShell   │  │  Dashboard   │  │   Chip UIs (Modular)     │  │
│  │  (PWA/Mobile)│  │  (Analytics) │  │   Idiomas · Finanzas ·   │  │
│  └──────┬───────┘  └──────┬───────┘  │   Reparto · Custom       │  │
│         │                 │          └────────────┬─────────────┘  │
│  ───────┴─────────────────┴──────────────────────┴──────────────── │
│                         REST API (FastAPI)                          │
│  ──────────────────────────────────────────────────────────────── │
│                                                                     │
│  ┌──────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────────┐   │
│  │ AI Host  │ │ Governance │ │ Knowledge  │ │  Communication  │   │
│  │ Engine   │ │ Engine     │ │ Graph      │ │  Layer          │   │
│  └──────────┘ └────────────┘ └────────────┘ └─────────────────┘   │
│                                                                     │
│  ┌──────────┐ ┌────────────┐ ┌────────────┐ ┌─────────────────┐   │
│  │ Module   │ │ Education  │ │ Skill      │ │  Stability      │   │
│  │ Registry │ │ Engine     │ │ Economy    │ │  Loop           │   │
│  └──────────┘ └────────────┘ └────────────┘ └─────────────────┘   │
│                                                                     │
│  ──────────────────────────────────────────────────────────────── │
│                    Distributed Infrastructure                       │
│  ┌────────────┐ ┌────────────────┐ ┌────────────┐ ┌────────────┐  │
│  │ Cluster    │ │ Digital        │ │ Mesh       │ │ Offline    │  │
│  │ Manager   │ │ Alexandria     │ │ Network    │ │ Runtime    │  │
│  └────────────┘ └────────────────┘ └────────────┘ └────────────┘  │
│                                                                     │
│  ──────────────────────────────────────────────────────────────── │
│                  SQLite + Migration Engine (30 migrations)          │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ✨ Key Features

### AI & Intelligence
- **AI Host** — Persistent AI orchestrator with 17+ command processors
- **Natural Language Interface** — Speak commands in English or Spanish
- **Leadership Detection** — Behavioral analysis for community governance
- **Hidden Skill Discovery** — AI-detected user strengths
- **Self-Healing** — Automated system auditing and auto-fix engine

### Distributed Infrastructure
- **Cluster Architecture** — Multi-node workload distribution
- **Mesh Networking** — Peer discovery without central authority
- **Offline-First** — Full functionality during disconnection with sync reconciliation
- **Digital Alexandria** — Fragmented, replicated storage grid

### Knowledge & Learning
- **Knowledge Graph** — Semantic connections between concepts
- **Education Engine** — Adaptive learning with personal skill trees
- **Skill Economy** — Expertise-based marketplace with real currency
- **Idea Cloud** — Collaborative ideation with AI clustering

### Communication
- **Natural Messaging** — `"write to Juan that I'll arrive later"`
- **Auto-Translation** — Messages translated to contact's language
- **Call Sessions** — Voice call scaffolding with cross-language support
- **Contact Graph** — Resolve contacts by name, nickname, or relationship

### Governance & Security
- **Reputation Graph** — Trust-weighted user connections
- **AI Governance Advisor** — Automated promotion recommendations
- **Role Hierarchy** — User → Beta Tester → Admin Candidate → Admin → Creator
- **Permission Engine** — Chip-level and operation-level access control
- **QR Access System** — Role-based entry via QR codes

### Platform
- **Chip System** — Modular plugin architecture for extensible apps
- **PWA Shell** — Mobile-first progressive web app
- **Mission Control** — 15-tab Creator cockpit for full system management
- **Accessibility** — Voice, text, subtitle, and braille scaffolding

---

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- pip

### Installation

```bash
# Clone the repository
git clone https://github.com/sionprograma/omniweb.git
cd omniweb

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt

# Launch OmniWeb
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Access Points
| Interface | URL |
|---|---|
| OmniShell (Main) | `http://localhost:8000/` |
| Dashboard | `http://localhost:8000/dashboard` |
| API Docs | `http://localhost:8000/api/v1/openapi.json` |
| Health Check | `http://localhost:8000/api/v1/system/health` |

### PWA Installation
Scan QR codes from `deployment/qr_access/` or navigate to the shell and select **"Add to Home Screen"** from your mobile browser.

---

## 📁 Repository Structure

```
omniweb/
├── backend/                    # FastAPI server & core modules
│   ├── core/                   # 60+ core system modules
│   │   ├── ai_host/            # AI Host with 17 command processors
│   │   ├── governance/         # Leadership detection & reputation graph
│   │   ├── communication/      # Natural language messaging & calls
│   │   ├── cluster/            # Distributed node management
│   │   ├── knowledge_graph/    # Semantic knowledge connections
│   │   ├── education_engine/   # Adaptive learning system
│   │   ├── stability_loop/     # Self-healing audit loop
│   │   └── ...                 # 50+ additional modules
│   ├── data/migrations/        # 30 SQL migration scripts
│   └── main.py                 # Application entry point
├── frontend/
│   ├── shell/                  # OmniShell PWA (Mission Control)
│   └── dashboard/              # Analytics dashboard
├── chips/                      # Modular plugin apps
│   ├── chip-idiomas-ia/        # AI Language Learning
│   ├── chip-finanzas/          # Financial Literacy
│   └── chip-reparto/           # Resource Distribution
├── runtime/                    # Standalone bootable runtime
├── infrastructure/             # Cluster & mesh configuration
├── deployment/                 # QR codes & deployment configs
├── docs/                       # Technical documentation
├── diagrams/                   # Mermaid architecture diagrams
└── whitepaper/                 # Technical whitepaper
```

---

## 📖 Documentation

| Document | Description |
|---|---|
| [Architecture](docs/architecture.md) | System architecture deep-dive |
| [AI Host](docs/ai_host.md) | AI orchestrator & processor pipeline |
| [Governance Model](docs/governance_model.md) | Leadership detection & reputation graph |
| [Communication Layer](docs/communication_layer.md) | Natural language messaging system |
| [Distributed Cluster](docs/distributed_cluster.md) | Node management & workload distribution |
| [Storage Grid](docs/storage_grid.md) | Digital Alexandria distributed storage |
| [Roadmap](docs/roadmap.md) | Development roadmap & milestones |
| [Open Source Modules](docs/open_source_modules.md) | Satellite repository strategy |
| [Whitepaper](whitepaper/omniweb_whitepaper.md) | Technical whitepaper |

---

## 🔐 Security & Governance

OmniWeb implements a multi-tier security model:

- **Role-Based Access Control** with chip-level permissions
- **Creator Override** for critical system operations
- **AI-Driven Governance** — automated leadership detection and promotion
- **Audit Trail** — full operation logging with rollback capability
- **QR-Based Access** — cryptographically distinct entry tokens per role

---

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on code style, pull requests, and chip development.

---

## 📜 License

MIT License. See [LICENSE](LICENSE) for details.

---

<p align="center">
  <strong>OmniWeb: Scaling Human Potential Through Collective Intelligence</strong><br/>
  <em>Built with 🧠 by the OmniWeb Engineering Team</em>
</p>
