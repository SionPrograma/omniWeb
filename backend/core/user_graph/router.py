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
    return {"status": "success", "message": "Personal knowledge graph rebuilt."}

@router.get("/query", response_model=GraphQueryResponse)
async def query_user_graph(current_user: OmniUser = Depends(get_current_user)):
    """
    Returns the full knowledge graph for the current user.
    """
    return user_graph_engine.get_user_graph(current_user.id)

@router.get("/neighbors")
async def get_node_neighbors(node_id: str, current_user: OmniUser = Depends(get_current_user)):
    """
    Returns neighbors and relationships for a specific node.
    """
    return user_graph_engine.get_neighbors(current_user.id, node_id)
