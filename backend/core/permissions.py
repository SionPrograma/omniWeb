import logging
from typing import Dict, Any, List, Optional
import contextvars
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class PermissionDeniedError(Exception):
    """Excepción lanzada cuando un chip intenta realizar una acción no permitida."""
    pass

# Context variable to store current chip slug. Default is None (untrusted)
_current_chip_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar("current_chip", default=None)

@contextmanager
def set_chip_context(slug: str):
    """
    Context manager to set the current executing chip slug globally for the current flow/async task.
    """
    token = _current_chip_ctx.set(slug)
    try:
        yield
    finally:
        _current_chip_ctx.reset(token)

def get_current_chip() -> Optional[str]:
    """Returns the currently active chip slug from context, or None if untrusted."""
    return _current_chip_ctx.get()

def enforce_permission(required_permission: str):
    """
    Verifica que el chip actual en ejecución tenga el permiso requerido.
    Si la llamada proviene del propio core (main.py, module_registry.py, etc) se permite.
    Levanta PermissionDeniedError si no tiene el permiso o el origen es desconocido.
    """
    chip_slug = get_current_chip()
    
    # 1. Si el contexto es 'core', el sistema central está operando de forma autorizada
    if chip_slug == "core":
        return

    # 1.5. Si no hay chip (ej. hilo en background desconectado), es Untrusted
    if not chip_slug:
        raise PermissionDeniedError(f"Origen de llamada desconocido o contexto perdido para '{required_permission}'.")

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
