import logging
import json
from typing import Dict, Any, Optional
from backend.core.education_engine.learning_path_generator import learning_path_generator
from backend.core.education_engine.concept_map_builder import concept_map_builder
from backend.core.ai_host.processors.supercommand_processor import AICommandResponse

logger = logging.getLogger(__name__)

class EducationProcessor:
    """Handles conversational learning requests."""
    
    async def process(self, topic: str, user_id: str) -> AICommandResponse:
        logger.info(f"Education: User requested to learn about {topic}")
        
        # 1. Generate Learning Path
        path = learning_path_generator.generate_path(topic)
        
        # 2. Build Concept Map
        cmap = concept_map_builder.build_map(topic)
        
        summary = f"He preparado una ruta de aprendizaje para **{topic}**.\n\n"
        summary += "Pasos iniciales:\n"
        for i, step in enumerate(path.steps[:3]):
            summary += f"{i+1}. {step.title}: {step.description}\n"
            
        summary += "\n¿Por dónde te gustaría empezar?"
        
        return AICommandResponse(
            intent="education_mentor",
            message=summary,
            status="success",
            payload={
                "path_id": path.id,
                "topic": topic,
                "map_root": cmap.name if cmap else topic
            }
        )

education_processor = EducationProcessor()
