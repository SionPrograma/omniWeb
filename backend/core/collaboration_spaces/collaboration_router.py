from fastapi import APIRouter, HTTPException, Depends
from .collaboration_manager import collab_manager
from .collaboration_models import CollabProject, ResearchNote, DomainCategory
from typing import List, Optional
from backend.core.auth import get_current_user, OmniUser

router = APIRouter()

@router.get("/projects")
async def list_projects(domain: Optional[str] = None, current_user: OmniUser = Depends(get_current_user)):
    projects = []
    if domain:
        try:
            projects = collab_manager.get_projects_by_domain(DomainCategory(domain))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid domain category")
    else:
        projects = list(collab_manager.projects.values())
        
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="list_collab_projects",
        status="success",
        message=f"Se han recuperado {len(projects)} proyectos de colaboración" + (f" en el dominio {domain}." if domain else "."),
        payload={"projects": [p.dict() if hasattr(p, 'dict') else p for p in projects]}
    )
    unified = await orchestrator.orchestrate("list collaboration projects", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/projects")
async def create_project(data: dict, current_user: OmniUser = Depends(get_current_user)):
    try:
        domain = DomainCategory(data.get("domain"))
        project = collab_manager.create_project(
            data.get("title"),
            data.get("description"),
            domain,
            current_user.id
        )
        
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        raw_res = AICommandResponse(
            intent="create_collab_project",
            status="success",
            message=f"Proyecto de colaboración '{project.title}' creado exitosamente.",
            payload={"project": project.dict() if hasattr(project, 'dict') else project}
        )
        unified = await orchestrator.orchestrate(f"create collaboration project {project.title}", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
        return {"status": "success", "payload": unified.model_dump()}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid domain category")

@router.post("/projects/{project_id}/join")
async def join_project(project_id: str, current_user: OmniUser = Depends(get_current_user)):
    project = collab_manager.join_project(project_id, current_user.id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.ai_host.processors.base import AICommandResponse
    orchestrator = CognitiveOrchestrator()
    raw_res = AICommandResponse(
        intent="join_collab_project",
        status="success",
        message=f"Te has unido al proyecto '{project.title}'.",
        payload={"project": project.dict() if hasattr(project, 'dict') else project}
    )
    unified = await orchestrator.orchestrate(f"join collaboration project {project_id}", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
    return {"status": "success", "payload": unified.model_dump()}

@router.post("/projects/{project_id}/notes")
async def add_project_note(project_id: str, note: dict, current_user: OmniUser = Depends(get_current_user)):
    from .collaboration_models import ResearchNote
    import uuid
    research_note = ResearchNote(
        id=str(uuid.uuid4()),
        author_id=current_user.id,
        content=note.get("content"),
        linked_concepts=note.get("linked_concepts", [])
    )
    if collab_manager.add_note(project_id, research_note):
        from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
        from backend.core.ai_host.processors.base import AICommandResponse
        orchestrator = CognitiveOrchestrator()
        raw_res = AICommandResponse(
            intent="add_collab_note",
            status="success",
            message="Nota de investigación añadida al proyecto.",
            payload={"note_id": research_note.id}
        )
        unified = await orchestrator.orchestrate(f"add note to project {project_id}", {"mode": "direct_response", "intent_group": "ECOSYSTEM"}, context={"user_id": current_user.id}, raw_response=raw_res)
        return {"status": "success", "payload": unified.model_dump()}
        
    raise HTTPException(status_code=404, detail="Project not found")
