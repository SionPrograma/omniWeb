from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status")
async def get_status():
    return {
        "chip": "safety_test",
        "status": "active",
        "message": "Backend for Original Chip is alive"
    }
