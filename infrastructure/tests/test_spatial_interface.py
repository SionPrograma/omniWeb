import pytest
from backend.core.spatial_interface.spatial_scene_manager import spatial_scene_manager
from backend.core.spatial_interface.spatial_layout_engine import spatial_layout_engine
from backend.core.spatial_interface.gesture_processor import gesture_processor
from backend.core.permissions import set_chip_context

@pytest.fixture(autouse=True)
def core_context():
    with set_chip_context("core"):
        yield

def test_add_hologram():
    obj = spatial_scene_manager.add_object("Test Agent", "agent")
    assert obj.name == "Test Agent"
    assert obj.id in spatial_scene_manager.objects

def test_spatial_arrangement():
    obj1 = spatial_scene_manager.add_object("Tool 1", "tool")
    obj2 = spatial_scene_manager.add_object("Tool 2", "tool")
    spatial_layout_engine.arrange_orbit([obj1, obj2])
    assert obj1.position.z != 0 or obj1.position.x != 0

def test_gesture_interaction():
    obj = spatial_scene_manager.add_object("Draggable", "tool")
    res = gesture_processor.process_gesture("move", obj.id, delta={"x": 5.0, "y": 0, "z": 0})
    assert res["status"] == "success"
    assert spatial_scene_manager.objects[obj.id].position.x > 4.0
