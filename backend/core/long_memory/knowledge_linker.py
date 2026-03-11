import logging
from .memory_models import MemoryLink
from .memory_store import memory_store

logger = logging.getLogger(__name__)

class KnowledgeLinker:
    """
    Links memories to chips, projects, and other system entities.
    """
    def link_to_chip(self, memory_id: int, chip_slug: str, relationship: str = "used_in"):
        link = MemoryLink(
            memory_id=memory_id,
            related_type="chip",
            related_id=chip_slug,
            relationship=relationship
        )
        memory_store.save_link(link)

    def link_to_workflow(self, memory_id: int, workflow_id: str):
        link = MemoryLink(
            memory_id=memory_id,
            related_type="workflow",
            related_id=workflow_id,
            relationship="workflow_context"
        )
        memory_store.save_link(link)

    def link_to_project(self, memory_id: int, project_id: str):
        link = MemoryLink(
            memory_id=memory_id,
            related_type="project",
            related_id=project_id,
            relationship="belongs_to"
        )
        memory_store.save_link(link)

knowledge_linker = KnowledgeLinker()
