# Distributed Cluster Architecture

## Overview

OmniWeb operates as a **distributed cluster** of autonomous nodes. Each node runs a complete OmniWeb runtime capable of independent operation, peer discovery, and workload distribution.

## Cluster Topology

```
              ┌──────────────┐
              │  Seed Node   │
              │  (Bootstrap) │
              └──────┬───────┘
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
  ┌──────────┐ ┌──────────┐ ┌──────────┐
  │  Node A  │ │  Node B  │ │  Node C  │
  │  Worker  │ │  Worker  │ │  Worker  │
  └────┬─────┘ └────┬─────┘ └────┬─────┘
       │             │             │
       └─────────────┼─────────────┘
                     │
              ┌──────┴───────┐
              │  Mesh Layer  │
              │  (Discovery) │
              └──────────────┘
```

## Node Types

| Type | Role | Count |
|---|---|---|
| **Seed Node** | Bootstrap, initial peer list | 1+ |
| **Worker Node** | General computation, storage, AI processing | N |
| **Edge Node** | Low-latency access point, CDN cache | N |
| **Offline Node** | Disconnected unit with local queue | N |

## Workload Distribution

The Cluster Manager (`core/cluster/`) handles:

1. **Task Scheduling**: Round-robin with health-weighted assignment
2. **Load Balancing**: Node capacity monitoring with automatic redistribution
3. **Failover**: Automatic task reassignment on node failure
4. **Priority Queues**: Critical operations processed first

### Workload Categories

| Priority | Category | Examples |
|---|---|---|
| P0 | System Health | Stability loop, self-healing |
| P1 | User Operations | AI queries, message sending |
| P2 | Background Tasks | Knowledge graph updates, sync |
| P3 | Analytics | Metrics aggregation, reports |

## Mesh Network Layer

The mesh network (`core/distributed_network/`) enables:

- **Zero-Config Discovery**: Nodes find peers without central DNS
- **Epidemic Gossip Protocol**: State propagation across the mesh
- **NAT Traversal Scaffolding**: Connections through firewalls
- **Heartbeat Monitoring**: 30-second health pulse from each node

## Offline Resilience

Each node maintains:
- Local operation queue (survives disconnection)
- Conflict-free data sync (CRDT-inspired merging)
- Autonomous AI Host (full capability without network)
- Periodic reconciliation on reconnect

## Event Distribution

The Distributed Bus (`core/distributed_bus/`) routes events:

```
┌──────────┐         ┌──────────────┐        ┌──────────────┐
│  Source   │ ──emit─→│  Event Bus   │──route─→│  Subscriber  │
│  Node    │         │  (Central)   │        │  Nodes       │
└──────────┘         └──────────────┘        └──────────────┘
```

Event types: `node.joined`, `node.left`, `task.assigned`, `task.completed`, `sync.requested`, `governance.insight`

## Scaling Strategy

| Metric | Current | Target |
|---|---|---|
| Max Nodes | 1 (development) | 100+ |
| Storage per Node | SQLite 500MB | 10GB+ per node |
| Network Protocol | HTTP REST | WebSocket + gRPC |
| Sync Latency | < 5s (LAN) | < 30s (WAN) |
