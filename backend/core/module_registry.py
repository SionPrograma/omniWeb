from fastapi import FastAPI, APIRouter
from typing import Dict, Any, List
import importlib
import logging

logger = logging.getLogger(__name__)

class ModuleRegistry:
    """
    Registry for OmniWeb modules.
    Ensures that modules can be registered and connected to the main backend.
    """
    def __init__(self):
        self.modules: Dict[str, Dict[str, Any]] = {}

    def register_module(self, app: FastAPI, module_name: str, router_import_path: str, prefix: str = None) -> bool:
        """
        Registers a module in the registry and includes its router in the main app.
        
        Args:
            app: The FastAPI application.
            module_name: Unique name for the module.
            router_import_path: Python import path to the module's router object.
            prefix: Optional API prefix for the module. Defaults to /module_name.
        """
        parts = router_import_path.split('.')
        module_path = '.'.join(parts[:-1])
        obj_name = parts[-1]
        
        try:
            # Intento 1: Asumir que router_import_path es `módulo.variable`
            # Ejemplo: modules.lingua.api.lingua_routes.router
            module = importlib.import_module(module_path)
            router = getattr(module, obj_name)
        except (ModuleNotFoundError, AttributeError) as e:
            # Si el error fue por una dependencia missing dentro del módulo, fallar explícitamente.
            if isinstance(e, ModuleNotFoundError) and getattr(e, 'name', None) != module_path:
                logger.error(f"Internal dependency error in module {module_name}: {e}")
                return False
                
            # Intento 2: Asumir que router_import_path es el módulo en sí (ej. router.py) 
            # y buscamos su variable 'router' exportada directamente
            try:
                module = importlib.import_module(router_import_path)
                router = getattr(module, 'router')
            except ModuleNotFoundError as e2:
                # Si el módulo en sí (o su versión .router) no existe, es un chip frontend-only
                if getattr(e2, 'name', None) in (router_import_path, module_path):
                    # Chip frontend-only. Es un comportamiento válido y omitimos error.
                    return True
                else:
                    logger.error(f"Internal dependency error in {router_import_path}: {e2}")
                    return False
            except AttributeError as e2:
                logger.error(f"Module {router_import_path} mapped for {module_name} doesn't export a 'router' attribute.")
                return False
        except Exception as e:
            logger.error(f"Unexpected error loading module {module_path}: {str(e)}")
            return False

        if not isinstance(router, APIRouter):
            logger.error(f"Object from {router_import_path} in module {module_name} is not an APIRouter.")
            return False
            
        final_prefix = prefix or f"/{module_name}"
        
        try:
            app.include_router(router, prefix=final_prefix, tags=[module_name])
            
            self.modules[module_name] = {
                "name": module_name,
                "prefix": final_prefix,
                "status": "active"
            }
            logger.info(f"Router registered for {module_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to include router for {module_name} in FastAPI app: {str(e)}")
            return False

    def get_active_modules(self) -> List[Dict[str, Any]]:
        """Returns a list of all active modules."""
        return list(self.modules.values())

module_registry = ModuleRegistry()
