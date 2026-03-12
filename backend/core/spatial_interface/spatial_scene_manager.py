import logging
from typing import Dict, List, Optional
from .spatial_models import SpatialScene, HologramObject, Vector3

logger = logging.getLogger(__name__)

class SpatialSceneManager:
    """Manages the lifecycle and state of the 3D holographic scene."""
    
    def __init__(self):
        self.active_scene = SpatialScene()
        self.objects: Dict[str, HologramObject] = {}

    def add_object(self, name: str, obj_type: str, position: Optional[Vector3] = None) -> HologramObject:
        obj = HologramObject(
            name=name,
            type=obj_type,
            position=position or Vector3(x=0, y=1.6, z=-2) # Default in front of user
        )
        self.objects[obj.id] = obj
        self.active_scene.objects.append(obj)
        logger.info(f"SpatialInterface: Added holographic {obj_type} - {name}")
        return obj

    def update_object(self, obj_id: str, position: Optional[Vector3] = None, 
                      rotation: Optional[Vector3] = None, scale: Optional[Vector3] = None):
        if obj_id in self.objects:
            obj = self.objects[obj_id]
            if position: obj.position = position
            if rotation: obj.rotation = rotation
            if scale: obj.scale = scale
            logger.debug(f"SpatialInterface: Updated object {obj_id}")

    def remove_object(self, obj_id: str):
        if obj_id in self.objects:
            self.active_scene.objects = [o for o in self.active_scene.objects if o.id != obj_id]
            del self.objects[obj_id]

spatial_scene_manager = SpatialSceneManager()
