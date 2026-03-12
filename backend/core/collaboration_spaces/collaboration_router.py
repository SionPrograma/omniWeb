from fastapi import APIRouter, HTTPException
from .collaboration_manager import collab_manager
from .collaboration_models import CollabProject, ResearchNote, DomainCategory
from typing import List, Optional

router = APIRouter()

@router.get("/projects")
async def list_projects(domain: Optional[str] = None):
    if domain:
        try:
            return collab_manager.get_projects_by_domain(DomainCategory(domain))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid domain category")
    return list(collab_manager.projects.values())

@router.post("/projects")
async def create_project(data: dict):
    try:
        domain = DomainCategory(data.get("domain"))
        return collab_manager.create_project(
            data.get("title"),
            data.get("description"),
            domain,
            data.get("user_id", "default_user")
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain category")

@router.post("/projects/{project_id}/join")
async def join_project(project_id: str, user_id: str = "default_user"):
    project = collab_manager.join_project(project_id, user_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project

@router.post("/projects/{project_id}/notes")
async def add_project_note(project_id: str, note: dict):
    from .collaboration_models import ResearchNote
    import uuid
    research_note = ResearchNote(
        id=str(uuid.uuid4()),
        author_id=note.get("author_id", "default_user"),
        content=note.get("content"),
        linked_concepts=note.get("linked_concepts", [])
    )
    if collab_manager.add_note(project_id, research_note):
        return {"status": "success"}
    raise HTTPException(status_code=404, detail="Project not found")
