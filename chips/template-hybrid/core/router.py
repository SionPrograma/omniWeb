from fastapi import APIRouter
from .service import template_service

router = APIRouter(tags=["Template"])

@router.get("/status")
async def get_status():
    """Ejemplo de endpoint que consume el servicio."""
    return template_service.get_system_status()
