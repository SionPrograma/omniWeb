# Architecture Overview: OmniWeb OS

OmniWeb is a **Personal Web Operating System** designed as a unified orchestrator for AI-powered productivity, knowledge management, and specialized utility modules (Chips).

## Core Philosophy: The Unified Modular Architecure

Unlike traditional monoliths or fragmented microfrontends, OmniWeb operates on a **Hybrid MPA (Multi-Page Application)** model. This approach maximizes resilience and isolation:

- **Strict Isolation**: A failure in the `Finance Chip` cannot compromise the `AI Host` or the `Identity Layer`.
- **Framework Agnosticism**: Each module (Chip) is a self-contained environment. While the shell is Vanilla JS, chips can be built with any technology.
- **Dynamic Orchestration**: The system discovers and mounts modules at runtime without code changes in the core router.

## High-Level Diagram

```mermaid
graph TD
    User((User)) --> Shell[OmniShell PWA]
    Shell --> AIHost[AI Host Orchestrator]
    Shell --> Dashboard[Creator Mission Control]
    
    subgraph Backend Core
        Router[System Router]
        Registry[Module Registry]
        Security[Security Fortress]
        State[System State Engine]
    end
    
    subgraph Autonomous Loop
        Auditor[System Auditor]
        AutoFix[AutoFix Engine]
        Insights[Insight Engine]
        Sync[Sync Engine]
    end
    
    subgraph persistence
        Logbook[Personal Logbook]
        Graph[Knowledge Graph]
    end

    Router --> Registry
    Registry --> C1
    Registry --> C2
    Registry --> C3
    Security --> Router
    State --> Dashboard
    Auditor --> AutoFix
    Insights --> AIHost
    Sync --> Logbook
    Logbook --> Graph
```

## System Components

### 1. The Kernel (Backend Core)
The Python-based kernel (FastAPI) handles the heavy lifting: resource orchestration, security enforcement, and cross-chip communication via a unified Event Bus.

### 2. The AI Host
The system's nervous system. It processes natural language, classifies intent, and delegates tasks to specialized processors or chips.

### 3. Personal Memory & Graph
The **Personal Logbook** records all user and system activity, which is then semantically mapped into a **Knowledge Graph** to derive relationships and long-term context.

### 4. Asset & Workspace Sync
Ensures multi-device consistency by synchronizing logs, graph data, and chip configurations using a conflict-safe LWW (Last Write Wins) strategy.

### 5. Autonomous Resilience
The **System Auditor** and **AutoFix Engine** continuously monitor the platform's health and apply patches or state corrections automatically, ensuring high uptime for the creator environment.
