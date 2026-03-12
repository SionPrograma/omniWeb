import logging
import math
from typing import List
from .spatial_models import Vector3, HologramObject

logger = logging.getLogger(__name__)

class SpatialLayoutEngine:
    """Calculates optimal arrangements for knowledge tools in 3D space."""
    
    def arrange_orbit(self, objects: List[HologramObject], radius: float = 2.0):
        """Places objects in a horizontal circle around the user."""
        count = len(objects)
        if count == 0: return
        
        angle_step = (2 * math.pi) / count
        for i, obj in enumerate(objects):
            angle = i * angle_step
            obj.position.x = radius * math.sin(angle)
            obj.position.z = radius * math.cos(angle)
            obj.position.y = 1.6 # Eye level
            # Face user logic simplified
            obj.rotation.y = angle * (180 / math.pi)

    def anchor_to_wall(self, obj: HologramObject, wall_normal: Vector3):
        """conceptual logic for environmental anchoring."""
        obj.is_anchored = True
        logger.info(f"SpatialLayout: Anchored object {obj.id} to wall.")

spatial_layout_engine = SpatialLayoutEngine()
