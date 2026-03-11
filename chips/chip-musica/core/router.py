from fastapi import APIRouter, HTTPException
from .service import music_service
from .schemas import MusicIdea, MusicIdeaCreate, MusicIdeaResponse

router = APIRouter()

@router.get("/ideas", response_model=MusicIdeaResponse)
async def list_ideas():
    """List all musical ideas saved in the system."""
    ideas = music_service.get_all_ideas()
    return MusicIdeaResponse(status="success", data=ideas)

@router.post("/ideas", response_model=MusicIdea)
async def create_idea(idea: MusicIdeaCreate):
    """Save a new musical idea or preset."""
    try:
        return music_service.save_idea(idea)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
