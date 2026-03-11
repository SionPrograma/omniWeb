import os
import sys
import platform
import socket
import logging
from enum import Enum

logger = logging.getLogger(__name__)

class EnvironmentType(Enum):
    DESKTOP = "desktop"
    SERVER = "server"
    CONTAINER = "container"
    PORTABLE = "portable"
    EMBEDDED = "embedded"

class EnvironmentDetector:
    """
    Detects the execution context of the OmniWeb platform.
    """
    def detect(self) -> EnvironmentType:
        # 1. Container Detection
        if os.path.exists('/.dockerenv') or os.environ.get('KUBERNETES_SERVICE_HOST'):
            return EnvironmentType.CONTAINER
            
        # 2. Portable Detection (USB/Specific path)
        cwd = os.getcwd().lower()
        if "usb" in cwd or "portable" in cwd or os.path.exists(os.path.join(cwd, ".omni_portable")):
            return EnvironmentType.PORTABLE
            
        # 3. Server vs Desktop (Heuristic based on OS and Display)
        system = platform.system().lower()
        
        # If linux and no DISPLAY, likely server
        if system == "linux":
            if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
                return EnvironmentType.SERVER
                
        # Windows Server check
        if system == "windows":
            if "server" in platform.release().lower():
                return EnvironmentType.SERVER

        # Default to Desktop for user convenience
        return EnvironmentType.DESKTOP

    def get_hostname(self) -> str:
        return socket.gethostname()

    def get_platform_info(self) -> dict:
        return {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor()
        }

environment_detector = EnvironmentDetector()
