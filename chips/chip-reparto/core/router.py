from fastapi import APIRouter
from pydantic import BaseModel
from typing import List, Dict, Any

router = APIRouter(tags=["Reparto"])

class StopStatusUpdate(BaseModel):
    status: str

# Transitional mock data en memoria (pseudo-DB)
mock_stops = [
    { "id": 1, "name": "Empresa de Transportes A", "address": "Av. Principal 123", "orderId": "RPT-001", "status": "PENDIENTE" },
    { "id": 2, "name": "Almacen Norte", "address": "Calle Industrial 45", "orderId": "RPT-002", "status": "PENDIENTE" },
    { "id": 3, "name": "Cliente VIP 1", "address": "Boulevard Central 89", "orderId": "RPT-003", "status": "PENDIENTE" },
    { "id": 4, "name": "Despacho B", "address": "Av. Costanera 101", "orderId": "RPT-004", "status": "PENDIENTE" },
]

@router.get("/stops", response_model=Dict[str, List[Dict[str, Any]]])
async def get_stops():
    """Retorna las paradas o entregas activas."""
    return {"stops": mock_stops}

@router.put("/stops/{stop_id}/status")
async def update_stop_status(stop_id: int, payload: StopStatusUpdate):
    """Actualiza el estado de una parada específica (transicionalmente en memoria)."""
    for stop in mock_stops:
        if stop["id"] == stop_id:
            stop["status"] = payload.status
            return {"success": True, "stop": stop}
    return {"success": False, "error": "Stop not found"}
