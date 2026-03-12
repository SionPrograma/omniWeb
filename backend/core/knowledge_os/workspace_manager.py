import logging
from typing import List, Optional
from .knowledge_os_models import WorkspaceState, InteractionMode

logger = logging.getLogger(__name__)

class WorkspaceManager:
    """Orchestrates the unified environment across spatial and desktop interfaces."""
    
    def __init__(self):
        self.state = WorkspaceState()

    def switch_mode(self, mode: InteractionMode):
        logger.info(f"KnowledgeOS: Switching environment mode to {mode}")
        self.state.current_mode = mode
        # Trigger related engine configurations
        if mode == InteractionMode.SPATIAL:
            from backend.core.spatial_interface.spatial_scene_manager import spatial_scene_manager
            spatial_scene_manager.active_scene.workspace_360 = True

    def mount_tool(self, tool_id: str):
        if tool_id not in self.state.active_tools:
            self.state.active_tools.append(tool_id)
            logger.info(f"KnowledgeOS: Tool {tool_id} mounted to workspace.")

    def unmount_tool(self, tool_id: str):
        if tool_id in self.state.active_tools:
            self.state.active_tools.remove(tool_id)

workspace_manager = WorkspaceManager()
