from typing import List, Dict
from .spatial_models import SpatialObject, Vector3D

class InteractionProjector:
    def __init__(self):
        self.active_projections: Dict[str, List[SpatialObject]] = {} # surface_id: objects

    def project_to_surface(self, surface_id: str, objects: List[SpatialObject]):
        """Simulates projecting spatial objects to a specific detected surface."""
        self.active_projections[surface_id] = objects
        return {
            "status": "projected",
            "surface": surface_id,
            "count": len(objects)
        }

    def update_projection(self, surface_id: str, obj_id: str, position: Vector3D):
        if surface_id in self.active_projections:
            for obj in self.active_projections[surface_id]:
                if obj.id == obj_id:
                    obj.position = position
                    return True
        return False

interaction_projector = InteractionProjector()
