from fastapi import APIRouter, Depends, HTTPException, Body
from typing import List, Optional, Dict, Any
from backend.core.security.dependencies import get_creator_user
from backend.core.auth import OmniUser
from backend.core.system_state.models import SystemMode
from .manager import creator_control_manager
from .audit_service import creator_audit_service

router = APIRouter()

@router.get("/status")
async def get_creator_control_status(creator: OmniUser = Depends(get_creator_user)):
    mode = await creator_control_manager.get_system_mode()
    maint = await creator_control_manager.get_active_maintenance()
    announcement = await creator_control_manager.get_active_announcement()
    
    status_data = {
        "mode": mode,
        "maintenance": maint,
        "announcement": announcement
    }
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="creator_control_status",
        status="success",
        message=f"Estado de control del Creador recuperado. Modo: {mode.upper()}.",
        payload=status_data
    )
    unified = await orchestrator.orchestrate("get creator control status", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": creator.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/mode")
async def set_system_mode(mode: SystemMode, creator: OmniUser = Depends(get_creator_user)):
    await creator_control_manager.set_system_mode(mode, creator.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="creator_control_mode",
        status="success",
        message=f"Modo del sistema actualizado a: {mode.upper()}.",
        payload={"new_mode": mode}
    )
    unified = await orchestrator.orchestrate(f"set system mode to {mode}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": creator.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/maintenance/schedule")
async def schedule_maintenance(
    start_time: str = Body(...),
    duration: int = Body(...),
    message: str = Body(...),
    creator: OmniUser = Depends(get_creator_user)
):
    await creator_control_manager.schedule_maintenance(start_time, duration, message, creator.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="creator_control_maintenance",
        status="success",
        message=f"Mantenimiento programado: {message}.",
        payload={"start_time": start_time, "duration": duration}
    )
    unified = await orchestrator.orchestrate("schedule maintenance", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": creator.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/announcement")
async def publish_announcement(
    message: str = Body(...),
    type: str = Body("INFO"),
    expires_in_minutes: int = Body(1440),
    creator: OmniUser = Depends(get_creator_user)
):
    await creator_control_manager.publish_announcement(message, type, creator.id, expires_in_minutes)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="creator_control_announcement",
        status="success",
        message=f"Anuncio global publicado: {message[:50]}...",
        payload={"message": message, "type": type}
    )
    unified = await orchestrator.orchestrate("publish announcement", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": creator.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/rollback")
async def force_rollback(label: str = Body(...), creator: OmniUser = Depends(get_creator_user)):
    try:
        res = await creator_control_manager.force_rollback(label, creator.id)
        
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        raw_res = AICommandResponse(
            intent="creator_control_rollback",
            status="success",
            message=f"Rollback forzado a la versión: {label}.",
            payload={"details": res}
        )
        unified = await orchestrator.orchestrate(f"force rollback to {label}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": creator.id}, raw_response=raw_res)
        return {"status": "success", "payload": unified.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/node/operation")
async def node_operation(
    node_id: str = Body(...),
    operation: str = Body(...), # 'drain', 'restart', 'disable', 'resume'
    creator: OmniUser = Depends(get_creator_user)
):
    from backend.core.security.manager import security_fortress
    security_fortress.log_creator_action(
        creator_id=creator.id,
        action_type="NODE_OPERATION",
        target=f"node:{node_id}",
        payload={"operation": operation}
    )
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="creator_control_node_op",
        status="success",
        message=f"Operación {operation} iniciada para el nodo {node_id}.",
        payload={"node_id": node_id, "operation": operation}
    )
    unified = await orchestrator.orchestrate(f"node operation {operation} on {node_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": creator.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/audit/summary")
async def get_audit_summary(limit: int = 15, creator: OmniUser = Depends(get_creator_user)):
    """
    OMNI_CREATOR_AUDIT_SURFACE — BLOCK 05: EVIDENCE AGGREGATION.
    Returns the unified evidence-first summary for the Creator.
    """
    summary = creator_audit_service.get_audit_summary(limit=limit)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="audit_summary",
        status="success",
        message=f"Se han consolidado {len(summary)} trazas de evidencia operacional.",
        payload={"audit_summary": summary}
    )
    unified = await orchestrator.orchestrate("get audit summary", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": creator.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
@router.get("/audit/debt")
async def get_audit_debt(limit: int = 10, creator: OmniUser = Depends(get_creator_user)):
    """
    OMNI_CREATOR_AUDIT_SURFACE — BLOCK 07: STRUCTURAL DEBT MONITOR.
    Returns clustered systemic drift and operational debt for the Creator.
    """
    debt = creator_audit_service.get_structural_debt(limit=limit)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="audit_debt",
        status="success",
        message=f"Se han identificado {len(debt)} clusters de deuda estructural.",
        payload={"debt_clusters": debt}
    )
    unified = await orchestrator.orchestrate("get structural debt", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": creator.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
