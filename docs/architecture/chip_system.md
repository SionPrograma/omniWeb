# Chip System: The Modular Standard

OmniWeb's extensibility relies on the **Chip Standard**. A Chip is a self-contained unit that follows a specific contract.

## Chip Manifest (`chip.json`)

Every chip must include a manifest declaring its identity and permissions:

```json
{
    "slug": "finance",
    "name": "Finance Hub",
    "version": "1.0.0",
    "type": "hybrid",
    "entry_frontend": "frontend/index.html",
    "permissions": ["storage_read", "storage_write", "personal_logbook"]
}
```

## Runtime Environment

- **Hybrid Chips**: Contain both a Python backend (FastAPI router) and a frontend.
- **Frontend-only**: Lightweight tools that leverage the shell's API.
- **Sandboxing**: Chips are isolated at the filesystem and network level unless they declare specific capabilities.

## Dynamic Generation

The **Chip Generator** allows the creator to bootstrap new modules instantly. It scaffolds:
1.  Standardized directory structure.
2.  Baseline `chip.json`.
3.  Vanilla frontend boilerplate.
4.  Standard Python router.

## Inter-Chip Communication

Chips communicate via the **Global Event Bus**. This allows a `Task Chip` to notify the `Dashboard` or trigger an `AI Host` event without direct coupling.
