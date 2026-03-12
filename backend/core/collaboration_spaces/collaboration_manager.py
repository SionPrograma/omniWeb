import uuid
from typing import Dict, List
from .collaboration_models import CollabProject, ResearchNote, DomainCategory

class CollaborationManager:
    def __init__(self):
        self.projects: Dict[str, CollabProject] = {}

    def create_project(self, title: str, description: str, domain: DomainCategory, creator_id: str) -> CollabProject:
        project_id = str(uuid.uuid4())
        project = CollabProject(
            id=project_id,
            title=title,
            description=description,
            domain=domain,
            creator_id=creator_id,
            participants=[creator_id]
        )
        self.projects[project_id] = project
        return project

    def join_project(self, project_id: str, user_id: str):
        if project_id in self.projects:
            if user_id not in self.projects[project_id].participants:
                self.projects[project_id].participants.append(user_id)
            return self.projects[project_id]
        return None

    def add_note(self, project_id: str, note: ResearchNote):
        if project_id in self.projects:
            self.projects[project_id].notes.append(note)
            # Here we would trigger semantic indexing
            return True
        return False

    def get_projects_by_domain(self, domain: DomainCategory) -> List[CollabProject]:
        return [p for p in self.projects.values() if p.domain == domain]

collab_manager = CollaborationManager()
