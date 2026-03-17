from fastapi import APIRouter, Depends, HTTPException, Body
from typing import Dict, Any, List
from backend.core.auth import OmniUser, get_current_user
from .manager import sync_manager
from .models import SyncPackage

router = APIRouter()

@router.post("/register")
async def register_device(
    device_id: str, 
    device_name: str, 
    metadata: Dict[str, Any] = {},
    user: OmniUser = Depends(get_current_user)
):
    """Registers a device for the current user."""
    success = sync_manager.register_device(user.id, device_id, device_name, metadata)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="sync_register",
        status="success" if success else "failed",
        message=f"Dispositivo '{device_name}' registrado exitosamente." if success else "Error al registrar dispositivo.",
        payload={"device_id": device_id, "success": success}
    )
    unified = await orchestrator.orchestrate(f"register device {device_name}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/devices")
async def list_devices(user: OmniUser = Depends(get_current_user)):
    """Lists registered sync devices."""
    devices = sync_manager.get_devices(user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="sync_list_devices",
        status="success",
        message=f"Se han encontrado {len(devices)} dispositivos vinculados.",
        payload={"devices": devices}
    )
    unified = await orchestrator.orchestrate("list my devices", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/package")
async def get_sync_package(user: OmniUser = Depends(get_current_user)):
    """Prepares an incremental sync package for the user."""
    package = sync_manager.prepare_package(user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="sync_get_package",
        status="success",
        message="Paquete de sincronización incremental preparado.",
        payload={"package": package.dict() if hasattr(package, 'dict') else package}
    )
    unified = await orchestrator.orchestrate("get sync package", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/ingest")
async def ingest_sync_package(
    package: SyncPackage,
    user: OmniUser = Depends(get_current_user)
):
    """Processes an incoming sync package."""
    if package.user_id != user.id:
        raise HTTPException(status_code=403, detail="Unauthorized sync target.")
    
    results = sync_manager.ingest_package(package)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="sync_ingest",
        status="success",
        message="Paquete de sincronización procesado e integrado correctamente.",
        payload={"results": results}
    )
    unified = await orchestrator.orchestrate("ingest sync package", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/status")
async def get_sync_status(user: OmniUser = Depends(get_current_user)):
    """Returns general sync health and recent logs."""
    from backend.core.database import db_manager
    from backend.core.permissions import set_chip_context
    
    with set_chip_context("core"):
        with db_manager.get_connection() as conn:
            logs = conn.execute(
                "SELECT * FROM sync_audit_logs WHERE user_id = ? ORDER BY timestamp DESC LIMIT 10",
                (user.id,)
            ).fetchall()
            devices = conn.execute("SELECT COUNT(*) as count FROM sync_devices WHERE user_id = ?", (user.id,)).fetchone()
            
            status_data = {
                "devices_count": devices["count"],
                "recent_logs": [dict(r) for r in logs],
                "health": "stable" if devices["count"] > 0 else "unconfigured"
            }
            
            from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
            from backend.core.ai_host.processors.base import AICommandResponse
            orchestrator = CognitiveOrchestrator()
            raw_res = AICommandResponse(
                intent="sync_status",
                status="success",
                message=f"Estado de sincronización: {status_data['health'].upper()}. {status_data['devices_count']} dispositivos activos.",
                payload=status_data
            )
            unified = await orchestrator.orchestrate("sync status", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": user.id}, raw_response=raw_res)
            return {"status": "success", "payload": unified.model_dump()}
