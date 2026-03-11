import logging
import platform
import os

logger = logging.getLogger(__name__)

class DeviceDetector:
    """
    Identifies the execution environment for OmniWeb.
    """
    def detect_environment(self) -> str:
        """
        Detects if running on Desktop, Mobile (simulated), or Container.
        """
        system = platform.system().lower()
        
        # Check for container
        if os.path.exists('/.dockerenv'):
            return "container"
            
        # Check for mobile (simple heuristic for demonstration)
        if "android" in system or "ios" in system:
            return "mobile"
            
        # Standard desktop
        if system == "windows" or system == "darwin" or system == "linux" :
            return "desktop"
            
        return "embedded"

device_detector = DeviceDetector()
