from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Dict, Any
from backend.core.auth import get_current_user, OmniUser
from .models import GraphNode, GraphEdge, GraphQueryResponse
from .engine import user_graph_engine

router = APIRouter()

@router.post("/build")
async def build_user_graph(current_user: OmniUser = Depends(get_current_user)):
    """
    Triggers a rebuild of the user's semantic knowledge graph.
    """
    await user_graph_engine.build_from_logbook(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="graph_build",
        status="success",
        message="Tu grafo de conocimiento personal ha sido reconstruido.",
        payload={"message": "Personal knowledge graph rebuilt."}
    )
    unified = await orchestrator.orchestrate("rebuild my graph", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/query")
async def query_user_graph(current_user: OmniUser = Depends(get_current_user)):
    """
    Returns the full knowledge graph for the current user.
    """
    data = user_graph_engine.get_user_graph(current_user.id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="graph_query",
        status="success",
        message="Grafo desplegado. Puedes ver las conexiones semánticas capturadas.",
        payload=data.dict() if hasattr(data, 'dict') else data
    )
    unified = await orchestrator.orchestrate("show my graph", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.get("/neighbors")
async def get_node_neighbors(node_id: str, current_user: OmniUser = Depends(get_current_user)):
    """
    Returns neighbors and relationships for a specific node.
    """
    neighbors = user_graph_engine.get_neighbors(current_user.id, node_id)
    
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="graph_neighbors",
        status="success",
        message=f"Expandiendo conexiones para el nodo: {node_id}",
        payload={"neighbors": neighbors}
    )
    unified = await orchestrator.orchestrate(f"neighbors for {node_id}", {"mode": "direct_response", "intent_group": "MEMORY"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}
