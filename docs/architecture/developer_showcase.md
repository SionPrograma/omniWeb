# Developer Showcase: Inside OmniWeb

## System Architecture Diagram

```mermaid
graph TD
    User((Creator/Tester))
    
    subgraph "Interface Layer"
        MC[Mission Control Cockpit]
        OG[Omniverse Gateway]
        QR[QR Entry System]
    end
    
    subgraph "Orchestration Layer"
        AIH[AI Host]
        SM[Runtime Manager]
        AM[AutoFix Engine]
    end
    
    subgraph "Core Intelligence"
        KG[Global Knowledge Graph]
        LP[Learning Path Engine]
        OE[Opportunity Engine]
        RE[Reputation Engine]
    end
    
    subgraph "Cluster Infrastructure"
        Mesh[P2P Mesh Network]
        Grid[Distributed Storage Grid]
        Edge[Edge Scaling Nodes]
    end

    User --> MC
    User --> OG
    User --> QR
    MC --> AIH
    OG --> KG
    AIH --> SM
    AIH --> AM
    SM --> Mesh
    Mesh --> Grid
    RE --> LP
    LP --> OE
    Grid --> KG
    Edge --> Mesh
```

## Module Map

- `/backend`: Core FastAPI services and API routes.
- `/runtime`: The standalone execution engine and boot logic.
- `/chips`: Modular logic units for transcription, translation, and finance.
- `/infrastructure`: Database migrations, cluster configuration, and storage grid managers.
- `/frontend`: The interactive shell and Mission Control UI.
- `/docs`: Technical whitepaper, architecture specs, and development roadmap.

---
*OmniWeb: The Foundation for a Decentralized Society.*
