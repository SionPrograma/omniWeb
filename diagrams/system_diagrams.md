# OmniWeb System Diagrams

## 1. Global Architecture

```mermaid
graph TB
    subgraph Frontend["🖥️ PRESENTATION"]
        Shell["OmniShell PWA"]
        Dashboard["Analytics Dashboard"]
        ChipUIs["Chip UIs"]
    end

    subgraph API["⚡ API GATEWAY"]
        FastAPI["FastAPI REST Engine"]
    end

    subgraph Intelligence["🧠 INTELLIGENCE"]
        AIHost["AI Host<br/>18 Processors"]
        Governance["Governance Engine"]
        Communication["Communication Layer"]
        KnowledgeGraph["Knowledge Graph"]
        Education["Education Engine"]
    end

    subgraph Infrastructure["🌍 INFRASTRUCTURE"]
        Cluster["Cluster Manager"]
        Mesh["Mesh Network"]
        StorageGrid["Digital Alexandria"]
        Sync["Sync Engine"]
        StabilityLoop["Stability Loop"]
    end

    subgraph Data["💾 PERSISTENCE"]
        SQLite["SQLite Database"]
        Migrations["30 Migration Scripts"]
        Logbook["Master Logbook"]
    end

    Shell --> FastAPI
    Dashboard --> FastAPI
    ChipUIs --> FastAPI
    FastAPI --> AIHost
    FastAPI --> Governance
    FastAPI --> Communication
    FastAPI --> KnowledgeGraph
    FastAPI --> Education
    AIHost --> Cluster
    Governance --> SQLite
    Communication --> SQLite
    KnowledgeGraph --> SQLite
    Cluster --> Mesh
    Cluster --> StorageGrid
    StorageGrid --> SQLite
    StabilityLoop --> AIHost
    Sync --> SQLite
    Logbook --> SQLite
```

## 2. Cluster Topology

```mermaid
graph TD
    Seed["🌱 Seed Node<br/>Bootstrap"]
    
    WorkerA["🔧 Worker A"]
    WorkerB["🔧 Worker B"]
    WorkerC["🔧 Worker C"]
    Edge["⚡ Edge Node"]
    Offline["📴 Offline Node"]

    Seed -->|"peer list"| WorkerA
    Seed -->|"peer list"| WorkerB
    Seed -->|"peer list"| WorkerC
    
    WorkerA <-->|"gossip"| WorkerB
    WorkerB <-->|"gossip"| WorkerC
    WorkerA <-->|"gossip"| WorkerC
    
    WorkerA -->|"cache"| Edge
    WorkerC -->|"sync"| Offline

    subgraph Mesh["Mesh Layer"]
        WorkerA
        WorkerB
        WorkerC
    end
```

## 3. AI Host Pipeline

```mermaid
flowchart LR
    Input["User Input"] --> Intent["Intent<br/>Classifier"]
    Intent --> Router["Command<br/>Router"]
    
    Router --> P1["Knowledge"]
    Router --> P2["Memory"]
    Router --> P3["Status"]
    Router --> P4["Communication"]
    Router --> P5["Governance"]
    Router --> P6["Healing"]
    Router --> P7["Guide"]
    Router --> PN["...18 total"]
    
    P1 --> Response["AI Response<br/>Engine"]
    P2 --> Response
    P3 --> Response
    P4 --> Response
    P5 --> Response
    P6 --> Response
    P7 --> Response
    PN --> Response

    Response --> Output["Formatted<br/>Response"]
```

## 4. Knowledge Graph Structure

```mermaid
graph LR
    subgraph Users["👤 Users"]
        U1["User A"]
        U2["User B"]
    end

    subgraph Knowledge["📚 Knowledge Units"]
        K1["Python Basics"]
        K2["Machine Learning"]
        K3["Data Science"]
        K4["Web Dev"]
    end

    subgraph Skills["⭐ Skills"]
        S1["Programming"]
        S2["Analytics"]
        S3["Design"]
    end

    subgraph Opportunities["💼 Opportunities"]
        O1["ML Engineer"]
        O2["Full Stack Dev"]
    end

    U1 -->|"studies"| K1
    U1 -->|"studies"| K2
    U2 -->|"studies"| K3
    U2 -->|"studies"| K4
    
    K1 -->|"prerequisite"| K2
    K2 -->|"relates"| K3
    K4 -->|"relates"| K1
    
    K1 -->|"builds"| S1
    K2 -->|"builds"| S2
    K3 -->|"builds"| S2
    
    S1 -->|"qualifies"| O2
    S2 -->|"qualifies"| O1
```

## 5. Communication Layer Flow

```mermaid
sequenceDiagram
    participant User
    participant AIHost as AI Host
    participant MIE as Message Intent Engine
    participant CM as Contact Manager
    participant TA as Translation Adapter
    participant ConvMem as Conversation Memory

    User->>AIHost: "write to Juan that I'll arrive late"
    AIHost->>MIE: parse_intent(command)
    MIE->>MIE: Extract recipient: "Juan", message: "I'll arrive late"
    MIE->>CM: resolve_contact(user_id, "Juan")
    CM-->>MIE: Contact(Juan, lang=en)
    MIE->>TA: translate("llegaré tarde", es → en)
    TA-->>MIE: "I will arrive late"
    MIE->>ConvMem: store_draft(draft)
    MIE-->>AIHost: pending_confirmation
    AIHost-->>User: "To: Juan\nOriginal: llegaré tarde\nTranslated: I will arrive late\nSend?"
    User->>AIHost: "confirm"
    AIHost->>MIE: confirm_send(message_id)
    MIE->>ConvMem: record_sent_message()
    MIE-->>AIHost: sent ✅
    AIHost-->>User: "Message sent to Juan ✅"
```

## 6. Governance Evolution

```mermaid
stateDiagram-v2
    [*] --> User: QR Scan / Registration
    User --> BetaTester: Beta QR Code
    BetaTester --> Onboarding: 10-Step Protocol
    Onboarding --> SkillDetection: AI Hidden Skill Detection
    SkillDetection --> AdminCandidate: Leadership Score ≥ 0.8
    AdminCandidate --> GovernanceTraining: Governance Foundation
    GovernanceTraining --> Administrator: Creator Approval
    Administrator --> [*]

    note right of SkillDetection
        Behavioral Analysis:
        - Reputation Score
        - Help Count
        - Bug Reports
        - Exploration Depth
    end note
```
