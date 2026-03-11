import logging
import asyncio
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

class ServiceStatus:
    STARTING = "starting"
    RUNNING = "running"
    STOPPED = "stopped"
    FAILED = "failed"

class ServiceManager:
    """
    Handles the lifecycle of core OmniWeb services.
    """
    def __init__(self):
        self.services: Dict[str, str] = {}
        self.health_checks: Dict[str, Any] = {}

    def register_service(self, name: str):
        self.services[name] = ServiceStatus.STOPPED
        logger.debug(f"ServiceManager: Registered service '{name}'")

    async def start_service(self, name: str):
        self.services[name] = ServiceStatus.STARTING
        try:
            # Simulated startup logic
            await asyncio.sleep(0.1)
            self.services[name] = ServiceStatus.RUNNING
            logger.info(f"ServiceManager: Started service '{name}'")
        except Exception as e:
            self.services[name] = ServiceStatus.FAILED
            logger.error(f"ServiceManager: Failed to start service '{name}': {e}")

    async def stop_service(self, name: str):
        self.services[name] = ServiceStatus.STOPPED
        logger.info(f"ServiceManager: Stopped service '{name}'")

    async def restart_service(self, name: str):
        await self.stop_service(name)
        await self.start_service(name)

    def get_service_health(self, name: str) -> dict:
        return {
            "name": name,
            "status": self.services.get(name, "unknown"),
            "timestamp": asyncio.get_event_loop().time()
        }

    def get_all_health(self) -> List[dict]:
        return [self.get_service_health(name) for name in self.services]

service_manager = ServiceManager()
