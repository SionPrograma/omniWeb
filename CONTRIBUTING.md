# Contributing to OmniWeb OS

Thank you for your interest in extending the OmniWeb ecosystem. We welcome contributions that align with our core principles: **Modularity, Resilience, and AI Orchestration**.

## 🚀 Creating a New Chip
The easiest way to contribute is by creating a new **Chip**. 

1.  **Clone the Repository**:
    ```bash
    git clone https://github.com/nicolasalejandroordonez/omniweb.git
    ```
2.  **Scaffold Your Chip**:
    Create a new directory in `chips/` named `chip-{your-slug}`.
3.  **Define the Manifest**:
    Create a `chip.json` following the [Chip Standard](docs/chip_system.md).
    ```json
    {
        "id": "chip-example",
        "slug": "example",
        "name": "Example Tool",
        "version": "1.0.0",
        "type": "hybrid",
        "has_frontend": true,
        "has_backend": true,
        "entry_frontend": "frontend/index.html",
        "permissions": ["storage_read"]
    }
    ```
4.  **Implement your Logic**:
    - Place frontend assets in `frontend/`.
    - Place the FastAPI router in `backend/router.py`.
5.  **Test Integration**:
    Launch the system and verify that your chip appears in the Dashboard and responds to AI Host commands.

## 🛠️ Modifying the Kernel
If you intend to modify the `backend/core` or the `OmnivShell`:
1.  **Open an Issue**: Describe the architectural improvement or fix you propose.
2.  **Strict Isolation**: Ensure that your changes do not break the "Strict Isolation" principle of the Hybrid MPA model.
3.  **Documentation**: Update relevant files in `docs/` to reflect any schema or protocol changes.

## 🎨 Style Guidelines
- **Vanilla First**: Avoid adding large frontend frameworks. Use modern CSS (Grid/Flexbox) and ES6+ features.
- **Explicit Permissions**: Never bypass the permission system. If your chip needs a new capability, propose it as a global permission constant in `backend/core/permissions.py`.
- **Descriptive Logging**: All system-level events should be logged to the `Master Logbook` with clear metadata.

---
OmniWeb is a platform for creators, by creators. We look forward to seeing what you build.
