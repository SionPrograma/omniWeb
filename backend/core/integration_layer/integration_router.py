from fastapi import APIRouter, Depends
from typing import List, Dict, Any
from .integration_registry import integration_registry

router = APIRouter(prefix="/system/integration", tags=["Integration Layer"])

@router.get("/status")
async def get_integration_status():
    """Returns the status of all active domain bridges."""
    return {
        "status": "active",
        "active_bridges": integration_registry.list_bridges(),
        "total_connections": len(integration_registry.list_bridges())
    }

@router.get("/health")
async def get_integration_health():
    """Health check for the integration layer."""
    return {"status": "healthy", "layer": "Integration Core"}
