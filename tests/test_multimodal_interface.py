import pytest
from backend.core.interface.voice_interface import voice_interface
from backend.core.interface.gesture_interface import gesture_interface
from backend.core.interface.visual_interface import visual_interface

def test_voice_interface():
    audio_data = b"fake-audio-payload"
    text = voice_interface.process_input(audio_data)
    assert isinstance(text, str)
    assert len(text) > 0

def test_gesture_interface():
    gesture = {"type": "swipe_right"}
    cmd = gesture_interface.process_input(gesture)
    assert cmd == "next"
    
    cmd_unknown = gesture_interface.process_input({"type": "dance"})
    assert cmd_unknown == "unknown_gesture"

def test_visual_interface():
    res = visual_interface.generate_chart(["Jan", "Feb"], [10, 20])
    assert "type" in res
    assert res["type"] == "chart-bar"
    assert "labels" in res["data"]
    
    panel = visual_interface.create_visual_payload("panel-stat", 42, "Total Users")
    assert panel["title"] == "Total Users"
    assert panel["data"] == 42
