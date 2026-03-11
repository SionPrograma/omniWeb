import logging
import importlib
import sys
from backend.core.module_registry import module_registry

logger = logging.getLogger(__name__)

class ModuleReloader:
    """
    Handles runtime reloading of chip modules.
    """
    def reload_chip(self, chip_slug: str) -> bool:
        """
        Attempts to reload a modified chip without server restart.
        """
        try:
            # 1. Clear existing module from sys.modules
            folder_name = f"chip-{chip_slug}" if not chip_slug.startswith("chip-") else chip_slug
            router_pkg = f"chips.{folder_name}.core.router"
            
            if router_pkg in sys.modules:
                logger.info(f"Clearing {router_pkg} from sys.modules for reload.")
                del sys.modules[router_pkg]
                
            # 2. Re-discover and re-register
            module_registry.discover_all_chips()
            
            # 3. Reload from registry update (which re-imports and re-mounts)
            logger.info(f"ModuleReloader: Chip {chip_slug} successfully reloaded into registry.")
            return True
        except Exception as e:
            logger.error(f"ModuleReloader: Reload failed: {e}")
            return False

module_reloader = ModuleReloader()
