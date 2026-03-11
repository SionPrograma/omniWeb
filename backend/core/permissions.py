import logging
from typing import Dict, Any, List

logger = logging.getLogger(__name__)

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
