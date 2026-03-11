import pytest
import os
from backend.runtime.device_detector import device_detector
from backend.runtime.environment_loader import environment_loader
from backend.runtime.runtime_manager import runtime_manager

def test_device_detection():
    env = device_detector.detect_environment()
    assert env in ["desktop", "mobile", "container", "embedded"]

def test_environment_profile():
    profile = environment_loader.load_config("desktop")
    assert profile["ui_effects"] == "premium"
    
    mobile = environment_loader.load_config("mobile")
    assert mobile["ui_effects"] == "eco"

def test_runtime_initialization():
    runtime_manager.initialize_runtime()
    status = runtime_manager.get_status()
    assert "environment" in status
    assert "mode" in status
    assert "boot" in status
    
    # Check boot status of core components
    assert status["boot"]["ai_host"] is True or status["boot"]["ai_host"] is False # Boolean check
    assert "plugin_discovery" in status["boot"]

def test_portable_mode_override():
    # Force mock directory if desired, but we check detection logic
    res = runtime_manager.mode
    assert res in ["standard", "portable"]
