from typing import Optional
from .ledger import forge_ledger

class ForgeConfigManager:
    """
    Sovereign Configuration Manager for worker chips.
    Mediates between environment defaults and Creator-approved strategic overrides.
    """
    
    async def get_provider(self, capability: str, default_provider: str) -> str:
        """
        Returns the active provider for a capability.
        Prioritizes auditable overrides from the Intelligence Forge.
        """
        override = await forge_ledger.get_active_provider(capability)
        return override if override and override != "DEFAULT" else default_provider

# Global singleton
forge_config_manager = ForgeConfigManager()
