from fastapi import APIRouter

router = APIRouter()

@router.get("/status")
def get_status():
    return {"status": "chip-idiomas is active and governing conversational linguistic logic"}
