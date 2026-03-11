from fastapi import FastAPI, APIRouter
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, ValidationError
import importlib
import logging
import json
import os

logger = logging.getLogger(__name__)

class ChipMetadata(BaseModel):
    """
    Schema for chip.json metadata.
    Ensures consistency across all OmniWeb modules.
    """
    id: str
    slug: str
    name: str
    description: str = "Sin descripción"
    version: str = "0.0.0"
    type: str = "unknown" # hybrid, frontend-only, placeholder
    has_frontend: bool = True
    has_backend: bool = False
    entry_frontend: Optional[str] = "frontend/index.html"
    dashboard_visible: bool = True
    permissions: List[str] = []
    active: bool = True # Plugin system: allows disabling chips without deleting them

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
        metadata_dict = self._load_metadata(module_name)
        metadata = ChipMetadata(**metadata_dict)
        
        # 1.1 Check if chip is active (Plugin Installer Logic)
        if not metadata.active:
            logger.info(f"Chip {module_name} is installed but INACTIVE. Skipping.")
            return False

        router_obj = self._discover_backend_router(module_name, router_import_path)
        
        # If no router is found (and no critical error occurred), it's a frontend-only chip
        if router_obj is None:
            self._register_module_state(module_name, None, metadata_dict)
            return True

        # 2. Validation
        if not self._validate_backend(module_name, router_obj, router_import_path):
            return False

        # 3. Mounting
        final_prefix = prefix or f"/{module_name}"
        success = self._mount_backend_router(app, router_obj, module_name, final_prefix)
        
        if success:
            self._register_module_state(module_name, final_prefix, metadata_dict)
            
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
        Loads and validates chip.json from the chip's directory.
        Follows the Discovery -> Validation pattern for metadata.
        """
        chip_path = f"chips/chip-{slug}/chip.json"
        
        if os.path.exists(chip_path):
            try:
                with open(chip_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                # Strong Pydantic Validation
                validated = ChipMetadata(**data)
                return validated.model_dump()
                
            except ValidationError as e:
                logger.error(f"Metadata validation error in chip '{slug}': {str(e)}")
            except Exception as e:
                logger.warning(f"Failed to load metadata for {slug}: {str(e)}")
        
        # Consistent Fallback using the schema
        return ChipMetadata(
            id=f"chip-{slug}",
            slug=slug,
            name=slug.capitalize(),
            description="Módulo detectado sin metadata válida (fallback)",
            version="0.0.0",
            type="unknown"
        ).model_dump()

    def get_active_modules(self) -> List[Dict[str, Any]]:
        """Returns a list of all active modules currently mounted."""
        return list(self.modules.values())

    def discover_all_chips(self) -> List[Dict[str, Any]]:
        """
        Scans the chips/ directory for any valid chip.json.
        This provides the base for the Plugin Installer.
        """
        chips = []
        chips_dir = "chips"
        if not os.path.exists(chips_dir):
            return []
            
        for folder in os.listdir(chips_dir):
            if folder.startswith("chip-") and os.path.isdir(os.path.join(chips_dir, folder)):
                slug = folder.replace("chip-", "")
                metadata = self._load_metadata(slug)
                chips.append(metadata)
        return chips

module_registry = ModuleRegistry()
