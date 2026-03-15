import logging
import asyncio
import os
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
            
        from backend.core.stability_loop.loop_controller import loop_controller

        async def do_boot():
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
            
            # 3. Phase 28: Standalone Service Stack - Centralized Orchestration
            core_services = [
                "ai_host", "event_bus", "knowledge_graph", "cluster_manager", 
                "mesh_manager", "offline_manager", "storage_manager", "idea_processor", 
                "node_monitor", "discovery"
            ]
            
            # Map logical services to actual startup calls
            from backend.core.cluster.manager import cluster_manager
            from backend.core.cluster.mesh import mesh_manager
            from backend.core.cluster.offline import offline_manager
            from backend.core.cluster.storage import storage_manager
            from backend.core.distributed_network.node_discovery import node_discovery
            from backend.core.distributed_bus.node_health_monitor import node_health_monitor
            from backend.core.idea_cloud.idea_background_processor import idea_background_processor
            
            for svc in core_services:
                service_manager.register_service(svc)
                # Specific startup calls for Phase 28/29
                if svc == "cluster_manager": await cluster_manager.start_monitor()
                elif svc == "mesh_manager": await mesh_manager.start()
                elif svc == "offline_manager": await offline_manager.start()
                elif svc == "storage_manager": await storage_manager.start()
                elif svc == "discovery": await node_discovery.start()
                elif svc == "node_monitor": await node_health_monitor.start()
                elif svc == "idea_processor": await idea_background_processor.start()
                
                await service_manager.start_service(svc)
                if svc not in self.state.active_services:
                    self.state.active_services.append(svc)

            # 4. Phase 28: Standalone Boot & Node Provisioning
            boot_source = os.getenv("OMNI_BOOT_SOURCE", "local_disk")
            self.state.boot_source = boot_source
            await self._provision_local_node()
            
            self._initialized = True
            logger.info(f"OmniWeb Bootable Runtime: READY. Mode: {profile.name.upper()} | Source: {boot_source.upper()}")
            return {"status": "success", "mode": profile.name, "boot_source": boot_source}

        # Boot via stability loop for verified startup
        await loop_controller.execute_task("system_boot", do_boot)

    async def _provision_local_node(self):
        """Phase 28: Auto-provisions the local node for cluster/standalone operation."""
        from backend.core.cluster.manager import cluster_manager
        import uuid
        import socket
        
        # Determine if we have a node_id
        node_id = os.getenv("OMNI_NODE_ID", f"node-{socket.gethostname()}")
        
        provision_data = {
            "node_id": node_id,
            "node_role": "primary", # Standalone boots default to primary
            "node_region": "local-standalone",
            "node_url": "http://localhost:8000",
            "node_secret": os.getenv("OMNI_NODE_SECRET", str(uuid.uuid4())[:16]),
            "connected_services": self.state.active_services
        }
        
        try:
            await cluster_manager.register_node(provision_data)
            self.state.metadata["node_id"] = node_id
            logger.info(f"RuntimeController: Node {node_id} provisioned successfully.")
        except Exception as e:
            logger.error(f"RuntimeController: Failed to provision lead node: {e}")

    def get_runtime_summary(self) -> dict:
        return {
            "environment": self.state.environment.value,
            "hostname": self.state.hostname,
            "profile": self.state.profile_name,
            "boot_source": self.state.boot_source,
            "runtime_mode": self.state.runtime_mode,
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
        loop_state, result = await loop_controller.execute_task(
            "switch_profile",
            do_switch,
            {"profile": profile_name}
        )
        return loop_state, result

runtime_controller = RuntimeController()
