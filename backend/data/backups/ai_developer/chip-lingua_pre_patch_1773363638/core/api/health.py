from fastapi import APIRouter
import time

router = APIRouter(prefix="/health", tags=["health"])

@router.get("/")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": time.time(),
        "version": "1.0.0-mvp"
    }
