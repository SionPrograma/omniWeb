import logging
import asyncio
from datetime import datetime
from .environment_detector import environment_detector, EnvironmentType
from .service_manager import service_manager
from .device_profile_manager import device_profile_manager
from .runtime_state import RuntimeState

logger = logging.getLogger(__name__)

class RuntimeController:
    """
    Central coordinator for the OmniWeb Runtime Foundation.
    """
    def __init__(self):
        self.state = RuntimeState()
        self._initialized = False

    async def initialize(self):
        if self._initialized:
            return
            
        logger.info("OmniWeb Runtime Foundation: Initializing...")
        
        # 1. Detect Environment
        env_type = environment_detector.detect()
        self.state.environment = env_type
        self.state.hostname = environment_detector.get_hostname()
        self.state.is_portable = (env_type == EnvironmentType.PORTABLE)
        
        # 2. Select and Apply Profile
        profile = device_profile_manager.get_profile(env_type)
        device_profile_manager.apply_profile(profile)
        self.state.profile_name = profile.name
        
        # 3. Register and Start Core Services
        core_services = [
            "ai_host", "event_bus", "knowledge_graph", 
            "long_memory", "self_improvement", "usage_analytics"
        ]
        for svc in core_services:
            service_manager.register_service(svc)
            await service_manager.start_service(svc)
            self.state.active_services.append(svc)
            
        self._initialized = True
        logger.info(f"OmniWeb Runtime Foundation: Ready. Mode: {profile.name.upper()} on {env_type.value.upper()}")

    def get_runtime_summary(self) -> dict:
        return {
            "environment": self.state.environment.value,
            "hostname": self.state.hostname,
            "profile": self.state.profile_name,
            "is_portable": self.state.is_portable,
            "uptime_seconds": self.state.get_uptime(),
            "services": service_manager.get_all_health()
        }

    async def switch_profile(self, profile_name: str):
        """
        Switches the active runtime profile dynamically.
        Uses Stability Loop integration for safety.
        """
        from backend.core.stability_loop.loop_controller import loop_controller
        
        async def do_switch():
            # Find profile
            for p in device_profile_manager.profiles.values():
                if p.name == profile_name:
                    device_profile_manager.apply_profile(p)
                    self.state.profile_name = p.name
                    return {"status": "success", "new_profile": p.name}
            raise ValueError(f"Profile {profile_name} not found")

        # Execute via stability loop
        result = await loop_controller.execute_task(
            task_name=f"Profile Switch to {profile_name}",
            action=do_switch
        )
        return result

runtime_controller = RuntimeController()
