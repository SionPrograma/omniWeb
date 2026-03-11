import logging
import inspect
from typing import Dict, Any, List, Optional

logger = logging.getLogger(__name__)

class PermissionDeniedError(Exception):
    """Excepción lanzada cuando un chip intenta realizar una acción no permitida."""
    pass

def _get_caller_chip() -> Optional[str]:
    """
    Inspecciona la pila de llamadas para determinar qué chip ejecuta el código.
    Retorna el slug del chip (ej: 'finanzas') o None si es una llamada del core_system.
    """
    for frame_info in inspect.stack():
        filename = frame_info.filename.replace("\\", "/") # Normalizar rutas
        if "chips/chip-" in filename:
            parts = filename.split("chips/chip-")
            if len(parts) > 1:
                # Extraer "finanzas" de "finanzas/core/repository.py"
                slug_part = parts[1].split("/")[0]
                return slug_part
    return None

def enforce_permission(required_permission: str):
    """
    Verifica que el chip actual en ejecución tenga el permiso requerido.
    Si la llamada proviene del propio core (main.py, module_registry.py, etc) se permite.
    Levanta PermissionDeniedError si no tiene el permiso.
    """
    chip_slug = _get_caller_chip()
    
    # 1. Si no hay chip detectado, es el sistema central operando (ej: dashboard o inicialización)
    if not chip_slug:
        return

    # Evitamos importación circular importando aquí
    from backend.core.module_registry import module_registry
    
    chip_info = module_registry.modules.get(chip_slug)
    
    # 2. Si el chip no está registrado, intentamos leer desde disco (Load-Time/Init-Time)
    if not chip_info:
        logger.debug(f"Resolver permiso init-time para '{chip_slug}' desde chip.json")
        import json
        import os
        chip_json_path = f"chips/chip-{chip_slug}/chip.json"
        if not os.path.exists(chip_json_path):
            raise PermissionDeniedError(f"Chip '{chip_slug}' inactivo o no registrado.")
        
        try:
            with open(chip_json_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        except Exception as e:
            logger.error(f"Error parseando {chip_json_path}: {e}")
            raise PermissionDeniedError(f"No se pudo leer la metadata de '{chip_slug}'.")
    else:
        metadata = chip_info.get("metadata", {})

    # 3. Validar metadata final
    if not check_permission(metadata, required_permission):
        raise PermissionDeniedError(f"Permiso '{required_permission}' denegado para chip '{chip_slug}'.")

def check_permission(chip_metadata: Dict[str, Any], required_permission: str) -> bool:
    """
    Checks if a chip has a specific permission declared in its metadata.
    This is a core helper for future security hardening.
    
    :param chip_metadata: Dictionary containing chip metadata (from chip.json)
    :param required_permission: The permission string to check for.
    :return: True if permission is present, False otherwise.
    """
    permissions = chip_metadata.get("permissions", [])
    
    if not isinstance(permissions, list):
        logger.warning(f"Chip {chip_metadata.get('slug', 'unknown')} has malformed permissions field.")
        return False
        
    result = required_permission in permissions
    
    if not result:
        logger.debug(f"Permission '{required_permission}' denied for chip '{chip_metadata.get('slug')}'")
        
    return result

def get_chip_permissions(chip_metadata: Dict[str, Any]) -> List[str]:
    """Returns the list of permissions for a given chip."""
    return chip_metadata.get("permissions", [])
