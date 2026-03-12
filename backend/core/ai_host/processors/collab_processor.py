import logging
from backend.core.collaboration_spaces.collaboration_manager import collab_manager, DomainCategory
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class CollaborationProcessor(CommandProcessor):
    """Bridges AI Host commands to the Collaboration Spaces system."""
    
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg = msg.lower()
        
        # 1. Create Project
        if "crear proyecto" in msg or "create project" in msg:
            # Simple simulation: Extracting title from "crear proyecto [TÍTULO]"
            title = msg.replace("crear proyecto", "").strip() or "Nuevo Proyecto de Colaboración"
            project = collab_manager.create_project(title, "Proyecto colaborativo iniciado vía AI Host.", DomainCategory.SCIENCE, user_id)
            
            return AICommandResponse(
                intent="collab_create",
                message=f"Proyecto '{project.title}' creado exitosamente en el dominio de Ciencia.",
                status="success",
                payload=project.model_dump()
            )

        # 2. Add research note
        if "nota de investigacion" in msg or "research note" in msg:
            projects = list(collab_manager.projects.values())
            if not projects:
                return AICommandResponse(intent="collab_err", message="No tienes proyectos activos para añadir notas.", status="error")
            
            target_project = projects[0]
            content = msg.replace("nota de investigacion", "").strip() or "Nuevos hallazgos en la investigación global."
            note = collab_manager.add_research_note(target_project.id, user_id, content)
            
            return AICommandResponse(
                intent="collab_note",
                message="Nota de investigación añadida y vinculada al Grafo de Conocimiento.",
                status="success",
                payload=note.model_dump()
            )

        return AICommandResponse(
            intent="collab_general",
            message="Comando de colaboración no reconocido. Prueba con 'crear proyecto El Origen de la Vida'.",
            status="partial"
        )

collab_processor = CollaborationProcessor()
