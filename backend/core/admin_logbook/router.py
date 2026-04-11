from fastapi import APIRouter, Depends, HTTPException
from typing import List, Dict, Any
from .manager import admin_manager
from .models import SuggestionStatus
from backend.core.auth import OmniUser, get_current_user, require_permission
from backend.core.governance.mode_registry import ModePermission

router = APIRouter()

@router.get("/logs")
async def get_admin_logs(admin_user: OmniUser = Depends(require_permission(ModePermission.SYSTEM_MAINTENANCE))):
    logs = admin_manager.list_operations()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="admin_logs",
        status="success",
        message=f"Se han recuperado {len(logs)} registros de operaciones administrativas.",
        payload={"logs": logs}
    )
    unified = await orchestrator.orchestrate("get admin logs", {"mode": "direct_response", "intent_group": "SYSTEM"}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/suggestions/pending")
async def get_pending_suggestions(admin_user: OmniUser = Depends(require_permission(ModePermission.GOVERNANCE_VIEW))):
    suggestions = admin_manager.get_pending_suggestions()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="admin_pending_suggestions",
        status="success",
        message=f"Hay {len(suggestions)} sugerencias pendientes de revisión.",
        payload={"suggestions": suggestions}
    )
    unified = await orchestrator.orchestrate("get pending suggestions", {"mode": "direct_response", "intent_group": "SYSTEM"}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/checkpoints")
async def list_checkpoints(admin_user: OmniUser = Depends(require_permission(ModePermission.GOVERNANCE_VIEW))):
    checkpoints = admin_manager.list_checkpoints()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="admin_list_checkpoints",
        status="success",
        message=f"Se encontraron {len(checkpoints)} puntos de restauración del sistema.",
        payload={"checkpoints": checkpoints}
    )
    unified = await orchestrator.orchestrate("list checkpoints", {"mode": "direct_response", "intent_group": "SYSTEM"}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/suggestions/{suggestion_id}/review")
async def review_suggestion(suggestion_id: str, status: SuggestionStatus, notes: str = "", admin_user: OmniUser = Depends(require_permission(ModePermission.SYSTEM_MAINTENANCE))):
    admin_manager.review_suggestion(suggestion_id, admin_user.id, admin_user.mode, status, notes)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="admin_review_suggestion",
        status="success",
        message=f"Sugerencia {suggestion_id} revisada ({status.value}).",
        payload={"suggestion_id": suggestion_id, "status": status.value}
    )
    unified = await orchestrator.orchestrate(f"review suggestion {suggestion_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id, "user_mode": admin_user.mode}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/checkpoint/create")
async def create_system_checkpoint(label: str, admin_user: OmniUser = Depends(require_permission(ModePermission.GOVERNANCE_EXECUTE))):
    path = admin_manager.create_checkpoint(admin_user.id, label)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="admin_create_checkpoint",
        status="success",
        message=f"Punto de restauración '{label}' creado exitosamente.",
        payload={"backup_path": path, "label": label}
    )
    unified = await orchestrator.orchestrate(f"create checkpoint {label}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id, "user_mode": admin_user.mode}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/rollback/{checkpoint_id}")
async def rollback_system(checkpoint_id: int, admin_user: OmniUser = Depends(require_permission(ModePermission.GOVERNANCE_EXECUTE))):
    try:
        admin_manager.rollback_to_checkpoint(checkpoint_id, admin_user.id)
        
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        raw_res = AICommandResponse(
            intent="admin_rollback",
            status="success",
            message=f"El sistema ha sido restaurado exitosamente al punto de control {checkpoint_id}.",
            payload={"checkpoint_id": checkpoint_id}
        )
        unified = await orchestrator.orchestrate(f"rollback to {checkpoint_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": admin_user.id, "user_mode": admin_user.mode}, raw_response=raw_res)
        return {"status": "success", "payload": unified.model_dump()}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
