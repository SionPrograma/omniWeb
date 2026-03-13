import logging
from typing import Dict, Any, Optional, List
from .base import CommandProcessor, AICommandResponse
from backend.core.module_registry import module_registry

logger = logging.getLogger(__name__)

class PermissionProcessor(CommandProcessor):
    """
    AI Host Processor for Chip Permissions.
    Phase 20: Capability & Sandbox Layer.
    """

    async def can_handle(self, command: str) -> bool:
        terms = ["permisos", "permissions", "capabilities", "access", "denied", "denegado"]
        cmd = command.lower()
        return any(term in cmd for term in terms)

    async def process(self, command: str, context: Optional[Dict[str, Any]] = None) -> AICommandResponse:
        cmd = command.lower()
        
        # 1. Querying specific chip permissions
        chips = module_registry.discover_all_chips()
        for chip in chips:
            if chip["slug"].lower() in cmd or chip["name"].lower() in cmd:
                perms = chip.get("permissions", [])
                text = f"### Permisos de '{chip['name']}'\n"
                if not perms:
                    text += "Este chip no tiene permisos declarados (Sandbox total)."
                else:
                    text += "\n".join([f"- `{p}`" for p in perms])
                
                # Check for restricted perms
                from backend.core.permissions import CREATOR_ONLY_PERMS
                restricted = [p for p in perms if p in CREATOR_ONLY_PERMS]
                if restricted:
                    text += f"\n\n⚠️ **Nota:** Este chip tiene capacidades de nivel Creador: {', '.join(restricted)}."

                return AICommandResponse(
                    intent="permission_query",
                    status="success",
                    message=text,
                    payload={"chip": chip["slug"], "permissions": perms}
                )

        # 2. Show chips with creator-only permissions
        if "creator" in cmd or "creador" in cmd:
            from backend.core.permissions import CREATOR_ONLY_PERMS
            text = "### Chips con Permisos de Creador\n"
            found = False
            for chip in chips:
                perms = chip.get("permissions", [])
                restricted = [p for p in perms if p in CREATOR_ONLY_PERMS]
                if restricted:
                    text += f"- **{chip['name']}**: {', '.join(restricted)}\n"
                    found = True
            if not found:
                text += "No se encontraron chips con permisos restringidos."
            return AICommandResponse(intent="permission_query", status="success", message=text)

        # 3. List all permissions (General)
        text = "### Seguridad y Capacidades de Chips\n"
        text += "OmniWeb utiliza un modelo de sandboxing donde cada chip declara sus permisos en `chip.json`.\n\n"
        text += "**Capacidades disponibles:**\n"
        from backend.core import permissions
        all_perms = [v for k,v in permissions.__dict__.items() if isinstance(v, str) and not k.startswith("_") and k.isupper()]
        text += ", ".join([f"`{p}`" for p in all_perms])
        
        return AICommandResponse(
            intent="permission_info",
            status="success",
            message=text
        )
