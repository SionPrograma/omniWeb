from fastapi import FastAPI, APIRouter
from typing import Dict, Any, List
import importlib
import logging
import json
import os

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
        Main orchestration for module registration.
        Follows the Discovery -> Validation -> Mounting pattern.
        """
        # 1. Discovery
        metadata = self._load_metadata(module_name)
        router_obj = self._discover_backend_router(module_name, router_import_path)
        
        # If no router is found (and no critical error occurred), it's a frontend-only chip
        if router_obj is None:
            self._register_module_state(module_name, None, metadata)
            return True

        # 2. Validation
        if not self._validate_backend(module_name, router_obj, router_import_path):
            return False

        # 3. Mounting
        final_prefix = prefix or f"/{module_name}"
        success = self._mount_backend_router(app, router_obj, module_name, final_prefix)
        
        if success:
            self._register_module_state(module_name, final_prefix, metadata)
            
        return success

    def _discover_backend_router(self, module_name: str, router_import_path: str) -> Any:
        """
        Responsibility: DISCOVERY.
        Attempts to locate the router object in the given Python import path.
        """
        parts = router_import_path.split('.')
        module_path = '.'.join(parts[:-1])
        obj_name = parts[-1]
        
        try:
            # Attempt 1: module.variable (e.g., chips.chip-reparto.core.router.router)
            module = importlib.import_module(module_path)
            return getattr(module, obj_name)
        except (ModuleNotFoundError, AttributeError) as e:
            # Check for critical internal errors (dependency missing inside the module)
            if isinstance(e, ModuleNotFoundError) and getattr(e, 'name', None) != module_path:
                logger.error(f"Internal dependency error in module {module_name}: {e}")
                raise e # Propagate critical loader errors
                
            # Attempt 2: module as a file (e.g., router.py) exporting 'router'
            try:
                module = importlib.import_module(router_import_path)
                return getattr(module, 'router')
            except ModuleNotFoundError as e2:
                # Valid case: Frontend-only chip (no backend found at all)
                if getattr(e2, 'name', None) in (router_import_path, module_path):
                    return None
                logger.error(f"Internal dependency error in {router_import_path}: {e2}")
                raise e2
            except AttributeError:
                # No 'router' attribute in the guessed path
                return None
        except Exception as e:
            logger.error(f"Unexpected discovery error for {module_name}: {str(e)}")
            return None

    def _validate_backend(self, module_name: str, router_obj: Any, path: str) -> bool:
        """
        Responsibility: VALIDATION.
        Checks if the discovered object meets the technical contract.
        """
        if not isinstance(router_obj, APIRouter):
            logger.error(f"Validation failed: Object from {path} in {module_name} is not an APIRouter.")
            return False
        return True

    def _mount_backend_router(self, app: FastAPI, router: APIRouter, module_name: str, prefix: str) -> bool:
        """
        Responsibility: MOUNTING.
        Integrates the validated router into the FastAPI application.
        """
        try:
            app.include_router(router, prefix=prefix, tags=[module_name])
            logger.info(f"Mounted router for {module_name} at {prefix}")
            return True
        except Exception as e:
            logger.error(f"Failed to mount router for {module_name}: {str(e)}")
            return False

    def _register_module_state(self, module_name: str, final_prefix: str, metadata: Dict[str, Any]):
        """
        Responsibility: STATE MANAGEMENT.
        Updates the internal dictionary with discovered module info.
        """
        self.modules[module_name] = {
            "name": metadata.get("name", module_name),
            "slug": module_name,
            "prefix": final_prefix,
            "status": "active" if final_prefix else "frontend-only",
            "metadata": metadata
        }


    def _load_metadata(self, slug: str) -> Dict[str, Any]:
        """
        Tries to load chip.json from the chip's directory.
        Fallback: returns basic structure with name and slug.
        """
        chip_path = f"chips/chip-{slug}/chip.json"
        
        if os.path.exists(chip_path):
            try:
                with open(chip_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load metadata for {slug}: {str(e)}")
        
        return {"name": slug.capitalize(), "slug": slug}

    def get_active_modules(self) -> List[Dict[str, Any]]:
        """Returns a list of all active modules."""
        return list(self.modules.values())

module_registry = ModuleRegistry()
