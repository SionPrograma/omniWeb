import logging
import re
from typing import Dict, Any, Optional
from .base import CommandProcessor, AICommandResponse
from backend.core.chip_generator.engine import chip_generator
from backend.core.module_registry import module_registry

logger = logging.getLogger(__name__)

class GeneratorProcessor(CommandProcessor):
    """
    AI Host Processor for Dynamic Chip Generation.
    Phase 13: Dynamic Chip Creation System.
    """

    async def can_handle(self, command: str) -> bool:
        terms = ["crear chip", "generar chip", "nuevo chip", "create chip", "generate chip", "new chip"]
        cmd = command.lower()
        return any(term in cmd for term in terms)

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = command.lower()
        
        # Regex to extract chip name
        # Examples: "create chip video_editor", "nuevo chip note-system"
        match = re.search(r"(?:create|generate|new|crear|generar|nuevo)\s+chip\s+([a-zA-Z0-9_\-]+)", cmd)
        
        if not match:
            return AICommandResponse(
                intent="generate_chip",
                status="error",
                message="No pude identificar el nombre del chip que quieres crear. Por favor usa el formato: 'crear chip [nombre]'",
                payload={}
            )
            
        slug = match.group(1).replace("-", "_").lower()
        
        # AI SAFETY (Phase 16): Check for explicit creator confirmation
        is_confirmed = "confirm" in cmd or (context.get("confirmed", False) if context else False)
        
        if not is_confirmed:
            return AICommandResponse(
                intent="confirmation_required",
                status="pending",
                message=f"### 🧪 Propuesta de Nuevo Chip\n¿Deseas generar el chip `{slug}`? Esto creará una nueva estructura de carpetas y archivos en el sistema.",
                payload={
                    "action": "generate_chip",
                    "slug": slug
                }
            )

        try:
            result = chip_generator.create_chip(slug)
            
            # Note: The chip will be detected automatically by the System State Engine 
            # as it scans the filesystem. To actually use it (API/Static), 
            # a system restart or dynamic reload would be needed. 
            # For this Phase, visibility in maps and system state is the priority.
            
            message = (
                f"### ✨ Chip '{result['metadata']['name']}' Generado con Éxito\n\n"
                f"He creado la estructura básica para el nuevo módulo en:\n"
                f"`{result['path']}`\n\n"
                f"**Archivos creados:**\n"
                f"- `chip.json`: Manifiesto y metadatos.\n"
                f"- `frontend/index.html`: Interfaz minimalista lista para usar.\n"
                f"- `backend/router.py`: Router inicial para endpoints del chip.\n\n"
                f"El chip aparecerá en unos segundos en tu **Galaxy Map** y en el cockpit de Mission Control."
            )
            
            return AICommandResponse(
                intent="generate_chip",
                status="success",
                message=message,
                payload=result
            )
            
        except FileExistsError as e:
            return AICommandResponse(
                intent="generate_chip",
                status="error",
                message=f"❌ El chip '{slug}' ya existe en el sistema. Por favor elige otro nombre.",
                payload={"error": str(e)}
            )
        except Exception as e:
            logger.error(f"Error generating chip: {e}")
            return AICommandResponse(
                intent="generate_chip",
                status="error",
                message=f"❌ Ocurrió un error al generar el chip: {str(e)}",
                payload={"error": str(e)}
            )
