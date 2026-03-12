from fastapi import APIRouter, Depends
from .context_model import context_model

router = APIRouter()

@router.get("/context")
async def get_user_context():
    patterns = context_model.get_patterns()
    return {
        "status": "ok",
        "patterns": patterns
    }
