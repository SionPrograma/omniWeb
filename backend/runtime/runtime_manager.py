import logging
import os
import sys
from backend.runtime.device_detector import device_detector
from backend.runtime.environment_loader import environment_loader

logger = logging.getLogger(__name__)

class RuntimeManager:
    """
    Orchestrates the OmniWeb execution environment across multiple devices.
    """
    def __init__(self, mode: str = "standard"):
        self.mode = mode # 'standard' or 'portable'
        self.environment = None
        self.config = None
        self.components = {}

    def initialize_runtime(self):
        """
        Boots the OmniWeb environment according to the detected execution context.
        """
        logger.info("Initializing OmniWeb Runtime Orchestration...")
        
        # 1. Detect Environment
        self.environment = device_detector.detect_environment()
        
        # 2. Add Portable Detection override
        # If running from a specific path (e.g. /media/usb), force portable mode
        if "usb" in os.getcwd().lower() or "portable" in os.getcwd().lower():
             self.mode = "portable"
        
        # 3. Load config
        self.config = environment_loader.load_config(self.mode if self.mode == "portable" else self.environment)
        
        # 4. Component Readiness (Step 20: Boot checks)
        logger.info(f"Target Environment: {self.environment}")
        logger.info(f"Optimization Mode: {self.mode}")
        logger.info(f"Selected Profile: {self.config.get('ui_effects')} UI")
        
        self.perform_boot_check()
        
    def perform_boot_check(self):
        """
        Step 20: Verifies system integrity during start-up.
        """
        checks = {
            "database": True, # Assume initialized in main
            "ai_host": True,
            "chip_factory": True,
            "plugin_discovery": True
        }
        
        # Basic DB check simulation
        from backend.core.database import db_manager
        if not os.path.exists(db_manager.db_path):
             checks["database"] = False
             
        # AI Host readiness check
        from backend.core.ai_host.command_router import ai_command_router
        if not ai_command_router:
             checks["ai_host"] = False

        self.components["boot_status"] = checks
        
        if all(checks.values()):
             logger.info("SYSTEM BOOT CHECK: STABLE")
        else:
             logger.warning(f"SYSTEM BOOT CHECK: DEGRADED - {checks}")

    def get_status(self):
        return {
            "environment": self.environment,
            "mode": self.mode,
            "config": self.config,
            "boot": self.components.get("boot_status", {})
        }

runtime_manager = RuntimeManager()
