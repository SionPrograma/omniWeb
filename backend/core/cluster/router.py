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

@router.get("/state", response_model=ClusterState)
async def get_cluster_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes the current state of the OmniWeb Node Cluster."""
    return await cluster_manager.get_cluster_state()

@router.get("/workload", response_model=WorkloadState)
async def get_workload_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes global workload distribution and task status."""
    return await workload_router.get_workload_state()

@router.post("/task/submit")
async def submit_cluster_task(chip_slug: str, context: dict, current_user: OmniUser = Depends(get_creator_user)):
    """Submits a chip task for cluster-wide distribution."""
    task_id = await workload_router.submit_task(chip_slug, context, current_user.id)
    return {"status": "task_submitted", "task_id": task_id}

@router.get("/mesh/state", response_model=MeshState)
async def get_mesh_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes the local mesh network view."""
    return await mesh_manager.get_mesh_state()

@router.post("/mesh/message")
async def send_mesh_message(target_node_id: str, payload: dict, current_user: OmniUser = Depends(get_creator_user)):
    """Routes a direct P2P message to a peer node."""
    # Logic to simulate P2P dispatch
    return await mesh_manager.process_p2p_message(current_user.id, payload)

@router.get("/offline/state", response_model=OfflineState)
async def get_offline_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes local autonomous mode status and backlog."""
    return await offline_manager.get_offline_state()

@router.get("/storage/state", response_model=StorageGridState)
async def get_storage_state(current_user: OmniUser = Depends(get_creator_user)):
    """Exposes global distributed storage health."""
    return await storage_manager.get_grid_state()

@router.post("/heartbeat")
async def post_heartbeat(payload: HeartbeatPayload):
    """
    Endpoint for nodes to report health.
    In Phase 24, we would verify the node signature/secret here.
    """
    # TODO: Verify node secret/signature
    await cluster_manager.process_heartbeat(payload)
    return {"status": "received"}

@router.post("/operation")
async def trigger_node_operation(op: NodeOperation, current_user: OmniUser = Depends(get_creator_user)):
    """Creator-only node control operations."""
    try:
        await cluster_manager.perform_node_operation(op.target_node_id, op.operation)
        return {"status": "success", "operation": op.operation, "target": op.target_node_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/failover")
async def trigger_failover(target_node_id: str, current_user: OmniUser = Depends(get_creator_user)):
    """Triggers manual primary node failover (Phase 24)."""
    await cluster_manager.promote_to_primary(target_node_id)
    return {"status": "failover_complete", "new_primary": target_node_id}

@router.post("/register")
async def register_node(node_data: dict, current_user: OmniUser = Depends(get_creator_user)):
    """Manually register or update a node (Creator only)."""
    await cluster_manager.register_node(node_data)
    return {"status": "node_registered"}
