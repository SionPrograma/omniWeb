import logging
from .spec_builder import SpecBuilder, ChipSpec
from .installer import ChipInstaller
from .validator import ChipValidator
from backend.core.module_registry import module_registry

logger = logging.getLogger(__name__)

class ChipFactory:
    """
    Orchestration engine for dynamic chip generation.
    """
    def __init__(self):
        self.builder = SpecBuilder()
        self.installer = ChipInstaller()
        self.validator = ChipValidator()

    async def create_from_request(self, user_prompt: str) -> dict:
        """
        Main workflow for chip generation.
        """
        logger.info(f"Generating chip for: {user_prompt}")
        
        # 1. Build Spec
        spec = self.builder.build_from_intent(user_prompt)
        
        # 2. Check duplicates in registry
        existing = module_registry.discover_all_chips()
        if any(c.get("slug") == spec.slug for c in existing):
            return {"status": "error", "detail": f"Un chip con el slug '{spec.slug}' ya existe."}

        try:
            # 3. Install
            chip_dir = self.installer.install(spec)
            
            # 4. Validate
            success, msg = self.validator.validate(chip_dir)
            if not success:
                self.installer.uninstall(spec.slug)
                return {"status": "error", "detail": f"Validación fallida: {msg}"}
            
            # 5. Return success
            return {
                "status": "success",
                "message": f"Chip '{spec.name}' generado y listo para activación.",
                "chip": {
                    "slug": spec.slug,
                    "name": spec.name,
                    "type": spec.type,
                    "location": chip_dir
                }
            }
            
        except Exception as e:
            logger.error(f"Error factory: {e}")
            return {"status": "error", "detail": str(e)}

chip_factory = ChipFactory()
