from fastapi import APIRouter
from typing import List, Dict, Any
from .schemas import Stop, StopStatusUpdate
from .service import reparto_service

router = APIRouter(tags=["Reparto"])

@router.get("/stops", response_model=Dict[str, List[Stop]])
async def get_stops():
    """Retorna las paradas o entregas activas (desde SQLite)."""
    stops = reparto_service.get_all_stops()
    return {"stops": stops}

@router.put("/stops/{stop_id}/status")
async def update_stop_status(stop_id: int, payload: StopStatusUpdate):
    """Actualiza el estado de una parada específica en la DB."""
    updated_stop = reparto_service.update_delivery_status(stop_id, payload.status)
    if updated_stop:
        return {"success": True, "stop": updated_stop}
    return {"success": False, "error": "Stop not found"}
