import logging
from typing import Dict, Any, Optional
from .spatial_scene_manager import spatial_scene_manager
from .spatial_models import Vector3

logger = logging.getLogger(__name__)

class GestureProcessor:
    """Simulates hand gesture recognition and interaction."""
    
    def process_gesture(self, gesture_type: str, obj_id: Optional[str] = None, 
                        delta: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Supported: grab, move, resize, rotate, dismiss.
        """
        if not obj_id and gesture_type != "dismiss_all":
            return {"status": "error", "message": "No object targeted"}

        if gesture_type == "dismiss":
            spatial_scene_manager.remove_object(obj_id)
            return {"status": "success", "action": "removed"}
            
        if gesture_type == "move" and delta:
            obj = spatial_scene_manager.objects.get(obj_id)
            if obj:
                obj.position.x += delta.get("x", 0)
                obj.position.y += delta.get("y", 0)
                obj.position.z += delta.get("z", 0)
                return {"status": "success", "action": "moved"}

        return {"status": "unsupported", "gesture": gesture_type}

gesture_processor = GestureProcessor()
