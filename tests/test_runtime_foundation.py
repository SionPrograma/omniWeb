import pytest
import asyncio
from backend.core.omni_runtime.environment_detector import environment_detector, EnvironmentType
from backend.core.omni_runtime.device_profile_manager import device_profile_manager
from backend.core.omni_runtime.service_manager import service_manager
from backend.core.omni_runtime.runtime_controller import runtime_controller

def test_environment_detection():
    # Since we're on Windows/Desktop, it should detect Desktop or Server
    env = environment_detector.detect()
    assert isinstance(env, EnvironmentType)

def test_profile_retrieval():
    profile = device_profile_manager.get_profile(EnvironmentType.DESKTOP)
    assert profile.name == "desktop"
    assert profile.resource_intensity == "high"
    
    eco_profile = device_profile_manager.get_profile(EnvironmentType.CONTAINER)
    assert eco_profile.name == "eco"

def test_service_lifecycle():
    async def run():
        service_manager.register_service("test_svc")
        assert service_manager.services["test_svc"] == "stopped"
        
        await service_manager.start_service("test_svc")
        assert service_manager.services["test_svc"] == "running"
        
        health = service_manager.get_service_health("test_svc")
        assert health["status"] == "running"
        
        await service_manager.stop_service("test_svc")
        assert service_manager.services["test_svc"] == "stopped"
        
    asyncio.run(run())

def test_runtime_controller_init():
    async def run():
        # Reset init for test
        runtime_controller._initialized = False
        await runtime_controller.initialize()
        assert runtime_controller._initialized == True
        assert len(runtime_controller.state.active_services) > 0
        
        summary = runtime_controller.get_runtime_summary()
        assert "environment" in summary
        assert "profile" in summary
        
    asyncio.run(run())
