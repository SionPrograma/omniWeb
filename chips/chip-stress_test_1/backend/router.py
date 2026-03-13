from fastapi import APIRouter
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/status")
async def get_status():
    return {
        "chip": "stress_test_1",
        "status": "active",
        "message": "Backend for Stress test 1 is alive"
    }
