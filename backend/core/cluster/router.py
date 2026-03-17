from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from backend.core.security.dependencies import get_creator_user
from backend.core.auth import OmniUser
from .models import ClusterState, HeartbeatPayload, NodeOperation, WorkloadState, StorageGridState
from .mesh import mesh_manager, MeshState
from .offline import offline_manager, OfflineState
from .storage import storage_manager
from .manager import cluster_manager
from .workload import workload_router

router = APIRouter()

@router.get("/state")
async def get_cluster_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes the current state of the OmniWeb Node Cluster."""
    state = await cluster_manager.get_cluster_state()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="cluster_state",
        status="success",
        message="Estado global del cluster recuperado.",
        payload=state.dict() if hasattr(state, 'dict') else state
    )
    unified = await orchestrator.orchestrate("get cluster state", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/workload")
async def get_workload_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes global workload distribution and task status."""
    state = await workload_router.get_workload_state()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="cluster_workload",
        status="success",
        message="Distribución de carga de trabajo procesada.",
        payload=state.dict() if hasattr(state, 'dict') else state
    )
    unified = await orchestrator.orchestrate("get workload state", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/task/submit")
async def submit_cluster_task(chip_slug: str, context: dict, current_user: OmniUser = Depends(get_creator_user)):
    """Submits a chip task for cluster-wide distribution."""
    task_id = await workload_router.submit_task(chip_slug, context, current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="cluster_task_submit",
        status="success",
        message=f"Tarea para {chip_slug} enviada al cluster (ID: {task_id}).",
        payload={"task_id": task_id, "chip_slug": chip_slug}
    )
    unified = await orchestrator.orchestrate(f"submit task for {chip_slug}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/mesh/state")
async def get_mesh_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes the local mesh network view."""
    state = await mesh_manager.get_mesh_state()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="mesh_state",
        status="success",
        message="Malla de red local identificada.",
        payload=state.dict() if hasattr(state, 'dict') else state
    )
    unified = await orchestrator.orchestrate("get mesh state", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/mesh/message")
async def send_mesh_message(target_node_id: str, payload: dict, current_user: OmniUser = Depends(get_creator_user)):
    """Routes a direct P2P message to a peer node."""
    res = await mesh_manager.process_p2p_message(current_user.id, payload)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="mesh_p2p_message",
        status="success",
        message=f"Mensaje P2P enviado al nodo {target_node_id}.",
        payload=res
    )
    unified = await orchestrator.orchestrate(f"send p2p message to {target_node_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/offline/state")
async def get_offline_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes local autonomous mode status and backlog."""
    state = await offline_manager.get_offline_state()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="offline_state",
        status="success",
        message="Estado de autonomía local verificado.",
        payload=state.dict() if hasattr(state, 'dict') else state
    )
    unified = await orchestrator.orchestrate("get offline state", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/storage/state")
async def get_storage_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes global distributed storage health."""
    state = await storage_manager.get_grid_state()
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="storage_grid_state",
        status="success",
        message="Grid de almacenamiento distribuido verificado.",
        payload=state.dict() if hasattr(state, 'dict') else state
    )
    unified = await orchestrator.orchestrate("get storage state", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/heartbeat")
async def post_heartbeat(payload: HeartbeatPayload):
    """
    Endpoint for nodes to report health.
    In Phase 24, we would verify the node signature/secret here.
    """
    await cluster_manager.process_heartbeat(payload)
    return {"status": "received"}

@router.post("/operation")
async def trigger_node_operation(op: NodeOperation, current_user: OmniUser = Depends(get_creator_user)):
    """Creator-only node control operations."""
    try:
        await cluster_manager.perform_node_operation(op.target_node_id, op.operation)
        
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        raw_res = AICommandResponse(
            intent="cluster_node_op",
            status="success",
            message=f"Operación {op.operation} ejecutada en nodo {op.target_node_id}.",
            payload={"operation": op.operation, "target": op.target_node_id}
        )
        unified = await orchestrator.orchestrate(f"cluster node operation {op.operation}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
        return {"status": "success", "payload": unified.model_dump()}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/failover")
async def trigger_failover(target_node_id: str, current_user: OmniUser = Depends(get_creator_user)):
    """Triggers manual primary node failover (Phase 24)."""
    await cluster_manager.promote_to_primary(target_node_id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="cluster_failover",
        status="success",
        message=f"Failover completado. Nodo {target_node_id} ahora es primario.",
        payload={"new_primary": target_node_id}
    )
    unified = await orchestrator.orchestrate(f"trigger failover to {target_node_id}", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/register")
async def register_node(node_data: dict, current_user: OmniUser = Depends(get_creator_user)):
    """Manually register or update a node (Creator only)."""
    await cluster_manager.register_node(node_data)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="cluster_node_register",
        status="success",
        message="Nodo registrado exitosamente en el cluster.",
        payload={"node_data": node_data}
    )
    unified = await orchestrator.orchestrate("register cluster node", {"mode": "direct_response", "intent_group": "SYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
