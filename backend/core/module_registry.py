from fastapi import FastAPI, APIRouter
from typing import Dict, Any, List
import importlib
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModuleRegistry:
    """
    Registry for OmniWeb modules.
    Ensures that modules can be registered and connected to the main backend.
    """
    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}

    def register_module(self, app: FastAPI, module_name: str, router_import_path: str, prefix: str = None):
        """
        Registers a module in the registry and includes its router in the main app.
        
        Args:
            app: The FastAPI application.
            module_name: Unique name for the module.
            router_import_path: Python import path to the module's router object.
            prefix: Optional API prefix for the module. Defaults to /module_name.
        """
        try:
            # Dynamically import the module's router
            module_path_parts = router_import_path.split('.')
            module_obj_name = module_path_parts.pop()
            router_module_path = '.'.join(module_path_parts)
            
            router_module = importlib.import_module(router_module_path)
            router = getattr(router_module, module_obj_name)
            
            if not isinstance(router, (APIRouter,)):
                logger.error(f"Module {module_name} error: {router_import_path} is not an APIRouter.")
                return False
                
            # If no prefix provided, use /module_name
            final_prefix = prefix if prefix else f"/{module_name}"
            
            # Include the router in the main app
            app.include_router(router, prefix=final_prefix, tags=[module_name])
            
            # Register in internal dictionary
            self.modules[module_name] = {
                "name": module_name,
                "prefix": final_prefix,
                "status": "active"
            }
            
            logger.info(f"Module '{module_name}' registered successfully with prefix {final_prefix}")
            return True
            
        except ImportError as e:
            logger.error(f"Failed to import module {module_name}: {str(e)}")
            return False
        except AttributeError as e:
            logger.error(f"Module {module_name} doesn't have the router object: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error registering module {module_name}: {str(e)}")
            return False

    def get_active_modules(self) -> List[Dict[str, Any]]:
        """Returns a list of all active modules."""
        return list(self.modules.values())

module_registry = ModuleRegistry()
