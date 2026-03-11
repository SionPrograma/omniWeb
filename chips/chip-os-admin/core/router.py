from fastapi import APIRouter, Security
from backend.core.database import db_manager
from backend.core.auth import get_admin_user
import os
import json

router = APIRouter()

@router.get("/logs")
def get_system_logs(limit: int = 100, admin_user: dict = Security(get_admin_user)):
    """
    Task 11: Observability tools. Reads the system_events bus history.
    Since chip.json specifies DB access, this is granted and safe.
    """
    with db_manager.get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM system_events ORDER BY timestamp DESC LIMIT ?", (limit,))
        rows = cursor.fetchall()
        return {"status": "ok", "events": [dict(row) for row in rows]}

@router.post("/plugins/{slug}/toggle")
def toggle_plugin_status(slug: str, active: bool, admin_user: dict = Security(get_admin_user)):
    """
    Task 9: Plugin installer approach. Safely modifies chip.json to enable/disable module.
    Changes take effect on next boot.
    """
    chip_path = f"chips/chip-{slug}/chip.json"
    if not os.path.exists(chip_path):
        return {"status": "error", "detail": "Chip no encontrado."}
    
    with open(chip_path, "r", encoding="utf-8") as f:
        metadata = json.load(f)
    
    metadata["active"] = active
    
    with open(chip_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=4)
        
    return {"status": "success", "message": f"Plugin {slug} set to {active}. Requires restart to take effect."}
