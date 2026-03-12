import logging
from .base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class MemoryProcessor(CommandProcessor):
    """
    Handles Command Memory Dialogue using Long Term Memory.
    """
    async def process(self, msg: str) -> AICommandResponse:
        from backend.core.long_memory.memory_retriever import memory_retriever
        
        # 1. Handle "continue/resume project"
        if any(keyword in msg for keyword in ["continuar", "resume", "proyecto"]):
            projects = memory_retriever.get_recent_projects()
            if projects:
                p = projects[0]
                return AICommandResponse(
                    intent="memory_recall",
                    status="success",
                    message=f"Hablemos de tu último proyecto: '{p.title}'. ¿Quieres continuar donde lo dejaste?",
                    payload={"memory": p}
                )
            return AICommandResponse(
                intent="memory_recall", 
                status="error", 
                message="No encontré proyectos recientes para continuar."
            )

        # 2. General recall
        memories = memory_retriever.find_relevant_memories(msg)
        if memories:
            m = memories[0]
            desc = f"He recordado esto: {m.summary}"
            return AICommandResponse(
                intent="memory_recall",
                status="success",
                message=desc,
                payload={"memories": memories}
            )
            
        return AICommandResponse(
            intent="memory_recall", 
            status="error", 
            message="No tengo recuerdos claros sobre eso aún."
        )
