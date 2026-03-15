import pytest
import uuid
from backend.core.collaboration_spaces.collaboration_manager import collab_manager
from backend.core.collaboration_spaces.collaboration_models import DomainCategory, ResearchNote

def test_create_and_join_project():
    project = collab_manager.create_project(
        title="Test Science Project",
        description="Exploring the unknown",
        domain=DomainCategory.SCIENCE,
        creator_id="user_1"
    )
    
    assert project.id in collab_manager.projects
    assert project.title == "Test Science Project"
    assert "user_1" in project.participants
    
    # Join
    updated_project = collab_manager.join_project(project.id, "user_2")
    assert "user_2" in updated_project.participants

def test_add_note():
    project = collab_manager.create_project(
        title="Note Project",
        description="Testing notes",
        domain=DomainCategory.ART,
        creator_id="user_1"
    )
    
    note = ResearchNote(
        id=str(uuid.uuid4()),
        author_id="user_1",
        content="First discovery"
    )
    
    success = collab_manager.add_note(project.id, note)
    assert success is True
    assert len(collab_manager.projects[project.id].notes) == 1
    assert collab_manager.projects[project.id].notes[0].content == "First discovery"

def test_get_projects_by_domain():
    collab_manager.create_project("Sci 1", "desc", DomainCategory.SCIENCE, "u1")
    collab_manager.create_project("Hist 1", "desc", DomainCategory.HISTORY, "u1")
    
    sci_projects = collab_manager.get_projects_by_domain(DomainCategory.SCIENCE)
    assert any(p.title == "Sci 1" for p in sci_projects)
    assert not any(p.title == "Hist 1" for p in sci_projects)
