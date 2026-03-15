# Digital Alexandria — Distributed Storage Grid

## Overview

The **Digital Alexandria** is OmniWeb's distributed storage system. Inspired by the ancient Library of Alexandria, it ensures that knowledge is fragmented, replicated, and permanently available — immune to censorship, single-point failures, or data loss.

## Architecture

```
┌──────────────────────────────────────────┐
│           Storage Grid Manager           │
│   (core/storage_grid/manager.py)         │
├──────────────────────────────────────────┤
│                                          │
│  ┌──────────┐  ┌──────────┐  ┌────────┐ │
│  │ Shard A  │  │ Shard B  │  │Shard C │ │
│  │ Node 1   │  │ Node 2   │  │Node 3  │ │
│  │ Replica→2│  │ Replica→1│  │Repli→1 │ │
│  └──────────┘  └──────────┘  └────────┘ │
│                                          │
│  ┌──────────┐  ┌──────────┐             │
│  │ Index    │  │ Integrity│             │
│  │ Service  │  │ Verifier │             │
│  └──────────┘  └──────────┘             │
└──────────────────────────────────────────┘
```

## Core Concepts

### Data Blocks
Every piece of knowledge stored in OmniWeb is split into **blocks**:

| Field | Description |
|---|---|
| `block_id` | Unique UUID identifier |
| `data_type` | `knowledge`, `conversation`, `skill_record`, `media` |
| `content_hash` | SHA-256 integrity checksum |
| `size_bytes` | Block payload size |
| `replication_count` | Number of copies across nodes |

### Sharding Strategy
- Files > 1MB are split into 256KB shards
- Each shard stored independently with integrity hash
- Minimum 2 replicas per shard (configurable)
- Shard map maintained by the Grid Manager

### Integrity Verification
- Periodic integrity sweeps compare `content_hash` against stored data
- Corrupted blocks trigger automatic re-replication from healthy nodes
- Full audit trail logged in the Master Logbook

## Operations

### Store
```python
grid_manager.store(data, data_type="knowledge", user_id="user123")
```
1. Data → fragment into blocks
2. Each block → content hash
3. Distribute across available nodes
4. Update shard index
5. Confirm replication

### Retrieve
```python
data = grid_manager.retrieve(block_id)
```
1. Lookup block in shard index
2. Fetch from nearest available node
3. Verify integrity hash
4. Return reconstructed data

### Delete
```python
grid_manager.delete(block_id, requester_id)
```
- Requires creator/admin permission
- Soft-delete with 7-day recovery window
- Hard-delete purges all replicas

## Replication Policies

| Policy | Replicas | Use Case |
|---|---|---|
| `standard` | 2 | General knowledge storage |
| `critical` | 3 | User credentials, system config |
| `archive` | 1 | Historical data, snapshots |
| `maximum` | N (all nodes) | Platform-critical data |

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/v1/system/storage/blocks` | List stored blocks |
| GET | `/api/v1/system/storage/stats` | Grid capacity metrics |
| POST | `/api/v1/system/storage/integrity` | Run integrity check |
| GET | `/api/v1/system/storage/block/{id}` | Retrieve specific block |

## Capacity Planning

| Metric | Current | Future |
|---|---|---|
| Block size | 256KB max | Configurable |
| Total capacity | Node-local | Distributed pool |
| Replication factor | 2x default | Dynamic based on importance |
| Integrity check interval | 1 hour | Configurable per node |
