# Chip Architecture: The Plug-and-Play Standard

OmniWeb's extensibility is powered by its **Modular Chip Standard**. This architecture allows for the rapid development and deployment of specialized tools without affecting the core kernel's stability.

## 1. Anatomy of a Chip
Every chip is a self-contained directory within the `chips/` folder, following a strict contract:

```text
chips/chip-{slug}/
├── chip.json          # The manifest (Identity & Permissions)
├── __init__.py        # Module entry point
├── frontend/          # Client-side resources
│   └── index.html     # Frontend entry
└── backend/           # Server-side logic
    ├── __init__.py
    └── router.py      # FastAPI router (API endpoints)
```

## 2. The Manifest (`chip.json`)
The `chip.json` file is the source of truth for the system. It defines:
- **Identity**: Name, slug, version, and type (hybrid/frontend/placeholder).
- **Entry Points**: Path to the `index.html` and router configuration.
- **Capabilities**: Declarative list of permissions (e.g., `storage_read`, `user_logbook_access`).

```json
{
    "id": "chip-finance",
    "slug": "finance",
    "name": "Finance Hub",
    "version": "1.0.0",
    "type": "hybrid",
    "has_frontend": true,
    "has_backend": true,
    "entry_frontend": "frontend/index.html",
    "permissions": ["storage_read", "storage_write"]
}
```

## 3. Runtime Discovery
The **Module Registry** automatically scans the `chips/` directory on startup. 
1. **Detection**: Locates directories with a valid `chip.json`.
2. **Validation**: Verifies that entry points exist and metadata is well-formed.
3. **Mounting**: 
   - Static files are served via a dynamic route `/chips/{slug}/static/`.
   - Backend routers are dynamically included in the main FastAPI application under `/api/v1/chips/{slug}/`.

## 4. The Plug-and-Play Experience
Because of this architecture:
- **Hot-swapping**: A chip can be added or updated by simply copying its folder.
- **Independence**: A crash in one chip's backend does not bring down the OmniWeb kernel.
- **Sandboxing**: Chips cannot access files or network resources unless explicitly declared in their permissions manifest.

## 5. Development Workflow
To create a new chip, the creator can use the **Chip Generator** system:
1. Issue the command: `"Generate a new chip for task management called TaskMaster"`
2. The AI Host scaffolds the directory structure and manifest.
3. The chip is immediately visible in the Dashboard and accessible via its reserved route.
