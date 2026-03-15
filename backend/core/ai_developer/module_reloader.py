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
            # Find the router path again
            possible_routers = [
                f"chips.chip-{chip_slug}.core.router",
                f"chips.chip-{chip_slug}.backend.router",
                f"chips.{chip_slug}.core.router",
                f"chips.{chip_slug}.backend.router"
            ]
            
            import os
            from backend.core.config import settings
            
            # Re-attempt registration if app is available
            if hasattr(module_registry, "app") and module_registry.app:
                for router_path in possible_routers:
                    # Check if router file exists before trying import (efficiency)
                    folder = chip_slug if chip_slug.startswith("chip-") else f"chip-{chip_slug}"
                    core_path = os.path.join("chips", folder, "core", "router.py")
                    back_path = os.path.join("chips", folder, "backend", "router.py")
                    
                    if os.path.exists(core_path) or os.path.exists(back_path):
                        logger.info(f"ModuleReloader: Re-registering {chip_slug} at runtime.")
                        module_registry.register_module(
                            app=module_registry.app,
                            module_name=chip_slug.replace("chip-", ""),
                            router_import_path=router_path,
                            prefix=f"{settings.API_V1_STR}/{chip_slug.replace('chip-', '')}"
                        )
                        break
            
            logger.info(f"ModuleReloader: Chip {chip_slug} successfully reloaded into registry.")
            return True
        except Exception as e:
            logger.error(f"ModuleReloader: Reload failed: {e}")
            return False

module_reloader = ModuleReloader()
