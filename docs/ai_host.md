# AI Host — Intelligent Orchestrator

## Overview

The **AI Host** is OmniWeb's persistent AI orchestrator. It manages system health, user mentorship, natural language routing, code analysis, governance advice, and communication — all through a unified command processor pipeline.

## Architecture

```
┌─────────────────────────────────────────────────┐
│                  AI HOST ENGINE                  │
├──────────┬──────────────────────────────────────┤
│          │        Intent Classifier              │
│  User    │              │                        │
│  Input ──┤     ┌────────┴────────┐               │
│          │     │ Command Router  │               │
│          │     └────────┬────────┘               │
│          │              │                        │
│          │  ┌───────────┼───────────┐            │
│          │  ▼           ▼           ▼            │
│          │ ┌──────┐ ┌──────┐ ┌──────────┐       │
│          │ │Proc 1│ │Proc 2│ │Proc N    │       │
│          │ └──────┘ └──────┘ └──────────┘       │
│          │              │                        │
│          │     ┌────────┴────────┐               │
│          │     │ Response Engine │               │
│          │     └─────────────────┘               │
└──────────┴──────────────────────────────────────┘
```

## Command Processors (18)

| Processor | Trigger Keywords | Function |
|---|---|---|
| `knowledge` | learn, study, conocimiento | Knowledge graph operations |
| `memory` | remember, recall, memoria | Long-term memory retrieval |
| `graph` | connections, relationships | User graph navigation |
| `supercommand` | `/deploy`, `/audit`, `/backup` | Admin supercommands |
| `logbook` | log, registro, journal | Master Logbook entries |
| `code_control` | patch, inspect, code | Source code analysis & patching |
| `healing` | fix, repair, heal | AutoFix sequence |
| `status` | status, health, estado | System health reports |
| `generator` | generate, create | Content/code generation |
| `user_logbook` | my log, mi diario | Personal user journal |
| `user_graph` | my network, mi red | Personal network visualization |
| `insight` | insight, perspectiva | AI-generated insights |
| `permission` | permissions, permisos | Access control queries |
| `leadership` | leadership, liderazgo | Beta tester onboarding flow |
| `guide` | what is, how do I, explain | Platform self-explanation |
| `governance_advisor` | governance, advisor | Governance recommendations |
| `communication` | write to, call, message | Natural language messaging |

## Processing Pipeline

```
1. User Input (text/voice)
         │
2. Intent Classification
         │
3. Processor Registry Scan
    ├── can_handle() checks
    └── First match wins
         │
4. Processor.process(msg, context)
         │
5. AICommandResponse
    ├── intent (string)
    ├── status (success/error/warning)
    ├── message (formatted response)
    └── payload (structured data)
         │
6. Response → Frontend
```

## Multimodal Support

The AI Host supports multimodal inputs via the `MultimodalRouter`:
- **Text**: Standard chat input
- **Voice**: Transcribed to text, processed normally
- **Image**: Visual analysis pipeline
- **Document**: Content extraction and analysis

## Antimodal System

The `AntimodalController` provides context-adaptive response modes:
- **Standard**: Normal AI responses
- **Minimal**: Reduced output for mobile/low-bandwidth
- **Technical**: Developer-focused responses
- **Mentor**: Educational guidance mode

## Stability Loop Integration

The AI Host participates in the system's self-healing cycle:
1. System Auditor runs probes
2. Issues detected → logged to Master Logbook
3. AutoFix Engine proposes patches
4. AI Host reviews and applies fixes
5. Re-audit confirms resolution

## Context Memory

Each user interaction maintains:
- **Session Context**: Current conversation state
- **Long-Term Memory**: Persistent user preferences and patterns
- **Development Memory**: Code changes and system modifications
- **Conversation History**: Timestamped interaction log

## API

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/api/v1/ai-host/process` | Process natural language command |
| GET | `/api/v1/ai-host/status` | AI Host health status |
| GET | `/api/v1/ai-host/processors` | List registered processors |
