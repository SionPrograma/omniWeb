from fastapi import APIRouter, Depends, Security, HTTPException, Request
from typing import Dict, Any, List
from .dependencies import get_creator_user
from .manager import security_fortress
from backend.core.auth import OmniUser
from backend.core.config import settings
from backend.core.system_auditor.auditor import auditor
from backend.core.system_auditor.fix_engine import fix_engine
from backend.core.chip_generator.engine import chip_generator
from backend.core.ai_developer.code_analyzer import code_analyzer
from pydantic import BaseModel
import os
import importlib

router = APIRouter()

@router.post("/device/register")
async def register_device(device_id: str, device_name: str, creator: OmniUser = Security(get_creator_user)):
    """
    Registers a new device for the designated creator.
    Note: Requires an already trusted device (or bootstrap session) to authorize.
    """
    key = security_fortress.register_device(creator.id, device_id, device_name)
    return {"status": "success", "signature_key": key}

@router.get("/inspect")
async def inspect_system(query: str, creator: OmniUser = Depends(get_creator_user)):
    security_fortress.log_creator_action(creator.id, "analyze", "filesystem", {"query": query})
    return code_analyzer.inspect_project(query)

@router.post("/audit")
async def run_audit(creator: OmniUser = Depends(get_creator_user)):
    security_fortress.log_creator_action(creator.id, "audit", "system_health", {})
    return await auditor.run_full_audit()

@router.post("/patch")
async def apply_patch(proposal_id: str, creator: OmniUser = Depends(get_creator_user)):
    security_fortress.log_creator_action(creator.id, "patch", f"proposal:{proposal_id}", {})
    success = await fix_engine.apply_fix(proposal_id)
    return {"status": "success" if success else "failed"}

@router.post("/generate_chip")
async def generate_chip(slug: str, name: str = None, creator: OmniUser = Depends(get_creator_user)):
    security_fortress.log_creator_action(creator.id, "generate_chip", f"chip:{slug}", {"name": name})
    try:
        res = chip_generator.create_chip(slug, name)
        return {"status": "success", "chip": res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/audit_trail")
async def get_audit_trail(limit: int = 50, creator: OmniUser = Depends(get_creator_user)):
    """
    Returns the recent security audit trail.
    """
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            rows = conn.execute(
                "SELECT * FROM security_audit_logs ORDER BY timestamp DESC LIMIT ?",
                (limit,)
            ).fetchall()
            return [dict(r) for r in rows]

# --- LIGHTWEIGHT CREATOR TOOLS (PART 3, 5, 6) ---

class FileSavePayload(BaseModel):
    path: str
    content: str

@router.post("/save-file")
async def save_file(payload: FileSavePayload, creator: OmniUser = Depends(get_creator_user)):
    """
    Saves a file to the project directory with safety checks.
    """
    # 1. Path validation (prevent path traversal)
    project_root = os.path.abspath(os.getcwd())
    target_path = os.path.abspath(os.path.join(project_root, payload.path))
    
    if not target_path.startswith(project_root):
        raise HTTPException(status_code=403, detail="Access denied: Path is outside project root.")
    
    # 2. Prevent access to sensitive files
    forbidden_segments = [".env", "database.db", "backend.db", "venv", ".venv", ".git"]
    for seg in forbidden_segments:
        if seg in target_path:
             raise HTTPException(status_code=403, detail=f"Access denied: Restricted segment '{seg}' found in path.")

    # 3. Save file safely
    try:
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        with open(target_path, "w", encoding="utf-8") as f:
            f.write(payload.content)
            
        # Log action
        security_fortress.log_creator_action(creator.id, "save_file", payload.path, {})

        # Part 6: Hot Reload (Backend)
        if target_path.endswith(".py") and "backend" in target_path:
            try:
                # Basic attempt to reload if already imported
                # In a real system, we'd map path to module name
                module_name = payload.path.replace("/", ".").replace("\\", ".").replace(".py", "")
                if module_name in sys.modules:
                    importlib.reload(sys.modules[module_name])
                    print(f"[HOT_RELOAD] Reloaded module: {module_name}")
            except Exception as re:
                print(f"[HOT_RELOAD] Failed to reload {payload.path}: {re}")
            
        return {"status": "success", "path": payload.path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

class CopilotPayload(BaseModel):
    prompt: str
    file: str

@router.post("/copilot")
async def creator_copilot(payload: CopilotPayload, creator: OmniUser = Depends(get_creator_user)):
    """
    Lightweight Copilot for Creator Mode.
    """
    security_fortress.log_creator_action(creator.id, "copilot_assist", payload.file, {"prompt": payload.prompt})
    
    # Simple placeholder logic for suggestion
    suggestion = f"// Suggestion for {payload.file}\n// Focus: {payload.prompt}\n\ndef modified_function():\n    # TODO: Implement based on creator request\n    pass"
    
    return {"suggestion": suggestion}
