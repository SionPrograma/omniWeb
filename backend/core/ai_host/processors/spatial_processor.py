import logging
from typing import Dict, Any, Optional
from backend.core.spatial_interface.spatial_scene_manager import spatial_scene_manager
from backend.core.spatial_interface.hologram_renderer import hologram_renderer
from backend.core.ai_host.processors.base import CommandProcessor, AICommandResponse

logger = logging.getLogger(__name__)

class SpatialProcessor(CommandProcessor):
    """Integrates natural language commands with the Spatial Interface Engine."""
    
    async def process(self, msg: str, user_id: str = "default_user") -> AICommandResponse:
        msg = msg.lower()
        
        # 1. Project Hologram
        if "proyectar" in msg or "project" in msg:
            obj_type = "tool"
            if "agente" in msg or "agent" in msg: 
                obj_type = "agent"
                if "investigaci" in msg or "research" in msg: name = "Investigador Holográfico"
                elif "tutor" in msg or "edu" in msg: name = "Tutor Virtual"
                elif "ingeniero" in msg or "engineer" in msg: name = "Ingeniero de Sistema"
            elif "mapa" in msg or "map" in msg: obj_type = "knowledge_map"
            elif "web" in msg: obj_type = "web_page"
            
            name = msg.split("project")[-1].split("proyectar")[-1].strip() or "Hologram"
            obj = spatial_scene_manager.add_object(name, obj_type)
            render = hologram_renderer.get_render_data(obj)
            
            return AICommandResponse(
                intent="spatial_project",
                message=f"Holograma de '{obj.name}' proyectado en el espacio de trabajo.",
                status="success",
                payload={"hologram": render}
            )

        # 2. Workspace View
        if "espacio" in msg and ("360" in msg or "workspace" in msg):
            return AICommandResponse(
                intent="spatial_workspace",
                message="Activando vista de espacio de trabajo 360 grados.",
                status="success",
                payload={"mode": "360_view"}
            )

        return AICommandResponse(
            intent="spatial_general",
            message="No entiendo el comando espacial. Prueba con 'proyectar agente' o 'espacio 360'.",
            status="partial"
        )

spatial_processor = SpatialProcessor()
