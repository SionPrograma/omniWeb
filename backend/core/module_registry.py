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
    active_backend: bool = False
    status: str = "ok" # ok, missing_router, damaged_backend, frontend_only
    entry_frontend: Optional[str] = "frontend/index.html"
    dashboard_visible: bool = True
    permissions: List[str] = []
    active: bool = True 
    installed: bool = True
    created_by: Optional[str] = "system"
    created_at: Optional[str] = None

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
        self.app = app # Store reference for dynamic re-loading
        # 1. Discovery
        metadata_dict = self._load_metadata(module_name)
        metadata = ChipMetadata(**metadata_dict)
        
        # 1.1 Check if chip is active (Plugin Installer Logic)
        if not metadata.active:
            logger.info(f"Chip {module_name} is installed but INACTIVE. Skipping.")
            return False

        # 1.2 Check if chip actually requires a backend
        if not metadata.has_backend:
            # Silently register state for frontend-only chips
            metadata_dict["active_backend"] = False
            metadata_dict["status"] = "frontend_only"
            self._register_module_state(module_name, None, metadata_dict)
            return True

        # 1.3 Pre-emptive Registration (Phase 1: Booting Resolve)
        # We register a partial state so that security layers can resolve the chip identity
        # while the import (which might trigger security checks) is still in progress.
        metadata_dict["status"] = "booting"
        self._register_module_state(module_name, prefix, metadata_dict)

        try:
            router_obj = self._discover_backend_router(module_name, router_import_path)
        except Exception as e:
             logger.error(f"REGISTRY: Chip '{module_name}' backend CRITICAL FAILURE: {e}")
             # We reload metadata to ensure we don't have partial state
             metadata_dict = self._load_metadata(module_name)
             metadata_dict["active_backend"] = False
             metadata_dict["status"] = "damaged_backend"
             self._register_module_state(module_name, prefix, metadata_dict)
             return False

        # If no router is found (and no critical error occurred)
        if router_obj is None:
            # We only error if metadata claimed a backend but none was found
            if metadata.has_backend:
                 logger.warning(f"Chip {module_name} claims to have a backend but no router was found at {router_import_path}.")
            metadata_dict["active_backend"] = False
            metadata_dict["status"] = "missing_router"
            self._register_module_state(module_name, None, metadata_dict)
            return True

        # 2. Validation
        if not self._validate_backend(module_name, router_obj, router_import_path):
            return False

        # 3. Mounting
        final_prefix = prefix or f"/{module_name}"
        success = self._mount_backend_router(app, router_obj, module_name, final_prefix)
        
        if success:
            metadata_dict["active_backend"] = True
            metadata_dict["status"] = "ok"
            self._register_module_state(module_name, final_prefix, metadata_dict)
            
        return success

    def _discover_backend_router(self, module_name: str, router_import_path: str) -> Any:
        """
        Responsibility: DISCOVERY.
        Attempts to locate the router object in the given Python import path.
        Optimized to handle cases where the module and the variable share names.
        """
        import types

        # Strategy A: Treat router_import_path as a module and look for '.router'
        # This is the standard: chips.chip-reparto.core.router -> module 'router' -> variable 'router'
        try:
            from backend.core.permissions import set_chip_context
            with set_chip_context(module_name):
                module = importlib.import_module(router_import_path)
            if hasattr(module, "router"):
                obj = getattr(module, "router")
                if isinstance(obj, APIRouter):
                    return obj
        except Exception as e:
            # Phase 0: Surgical Backend Isolation
            error_str = str(e)
            
            # Case 1: Router is truly missing (intentional Frontend-only)
            if "No module named" in error_str and router_import_path in error_str:
                logger.info(f"REGISTRY: Chip '{module_name}' has no backend router. Treating as Frontend-only.")
                return None
            
            # Case 2: Router exists but has internal dependency issues
            if "No module named" in error_str and router_import_path not in error_str:
                logger.error(f"REGISTRY: Internal dependency error in chip '{module_name}': {e}")
                # We return None to prevent boot crash, but we will mark as damaged in caller
                raise e # We re-raise to be caught by register_module for status tagging
            
            # Case 3: Security Denials or logic errors during import (Import-time DB access)
            logger.warning(f"REGISTRY: Backend discovery for '{module_name}' failed during import: {e}")
            raise e # Caught by register_module

        # Strategy B: Treat last part as variable name in parent module
        # This handles: chips.chip-reparto.core.router.router or modules.my_module.app
        parts = router_import_path.split('.')
        if len(parts) > 1:
            module_path = '.'.join(parts[:-1])
            obj_name = parts[-1]
            try:
                from backend.core.permissions import set_chip_context
                with set_chip_context(module_name):
                    module = importlib.import_module(module_path)
                    obj = getattr(module, obj_name)
                # If we found a module instead of an APIRouter, avoid returning it (prevents false positives)
                if isinstance(obj, APIRouter):
                    return obj
                if isinstance(obj, (types.ModuleType,)):
                    # If it's a module, maybe we should look inside? 
                    if hasattr(obj, "router"):
                        inner_obj = getattr(obj, "router")
                        if isinstance(inner_obj, APIRouter):
                            return inner_obj
            except (ModuleNotFoundError, AttributeError):
                pass
            except Exception as e:
                logger.debug(f"Strategy B failed for {module_name} at {module_path}")

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
        # If no status was set during discovery, use default logic
        current_status = metadata.get("status")
        if not current_status or current_status == "ok":
            current_status = "active" if final_prefix else ("unloaded_backend" if metadata.get("has_backend") else "frontend-only")

        self.modules[module_name] = {
            "name": metadata.get("name") if isinstance(metadata, dict) else metadata.name,
            "slug": module_name,
            "prefix": final_prefix,
            "status": current_status,
            "health": metadata.get("health", "unverified") if isinstance(metadata, dict) else "unverified",
            "active_backend": metadata.get("active_backend", False) if isinstance(metadata, dict) else getattr(metadata, "active_backend", False),
            "last_execution": None,
            "metadata": metadata if isinstance(metadata, dict) else metadata.dict()
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

    def activate_chip(self, slug: str) -> bool:
        """Enables a chip by setting its active status to True in chip.json."""
        return self._set_chip_active_status(slug, True)

    def deactivate_chip(self, slug: str) -> bool:
        """Disables a chip by setting its active status to False in chip.json."""
        return self._set_chip_active_status(slug, False)

    def _set_chip_active_status(self, slug: str, status: bool) -> bool:
        chip_path = f"chips/chip-{slug}/chip.json"
        if not os.path.exists(chip_path):
            return False
            
        try:
            with open(chip_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            data["active"] = status
            
            with open(chip_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            
            logger.info(f"Chip {slug} status set to {status}")
            return True
        except Exception as e:
            logger.error(f"Failed to update chip {slug} status: {e}")
            return False

    def search_chip(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Robust chip search by slug or name using prioritized matching.
        """
        all_chips = self.discover_all_chips()
        # Clean query
        clean_query = query.lower().strip()
        
        # Priority 1: Exact slug match
        for c in all_chips:
            if c["slug"].lower() == clean_query:
                return c
        
        # Priority 2: Query is in slug or name
        for c in all_chips:
            if clean_query in c["slug"].lower() or clean_query in c.get("name", "").lower():
                return c
                
        return None

    def log_execution(self, slug: str):
        """Simple tracker for UI feedback."""
        import datetime
        if slug in self.modules:
            self.modules[slug]["last_execution"] = datetime.datetime.now().isoformat()

    def get_module_data(self, slug: str) -> Optional[Dict[str, Any]]:
        return self.modules.get(slug)

module_registry = ModuleRegistry()
