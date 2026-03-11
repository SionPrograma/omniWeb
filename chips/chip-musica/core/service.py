from typing import List
from .repository import music_repo
from .schemas import MusicIdea, MusicIdeaCreate

class MusicService:
    """
    Business logic layer for the Music Chip.
    """
    def get_all_ideas(self) -> List[MusicIdea]:
        return music_repo.get_all()

    def save_idea(self, idea_data: MusicIdeaCreate) -> MusicIdea:
        # Create a domain object from input data
        new_idea = MusicIdea(
            id=0, # Placeholder
            title=idea_data.title,
            content=idea_data.content,
            scale_context=idea_data.scale_context,
            created_at="" # Will be set by repo
        )
        return music_repo.add(new_idea)

# Global instance
music_service = MusicService()
