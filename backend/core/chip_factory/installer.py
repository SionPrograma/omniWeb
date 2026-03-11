import os
import shutil
import logging
from .templates import ChipTemplates

logger = logging.getLogger(__name__)

class ChipInstaller:
    """
    Physically installs a chip into the filesystem.
    """
    def install(self, spec, target_root: str = "chips/") -> str:
        chip_folder = os.path.join(target_root, f"chip-{spec.slug}")
        
        if os.path.exists(chip_folder):
            raise FileExistsError(f"Chip {spec.slug} already exists.")

        os.makedirs(chip_folder)
        os.makedirs(os.path.join(chip_folder, "frontend"))
        if spec.type == "hybrid":
            os.makedirs(os.path.join(chip_folder, "core"))

        # 1. Create chip.json
        with open(os.path.join(chip_folder, "chip.json"), "w", encoding="utf-8") as f:
            f.write(ChipTemplates.get_chip_json_template(spec))

        # 2. Create index.html
        with open(os.path.join(chip_folder, "frontend", "index.html"), "w", encoding="utf-8") as f:
            f.write(ChipTemplates.get_frontend_template(spec))

        # 3. Create router.py if hybrid
        if spec.type == "hybrid":
            with open(os.path.join(chip_folder, "core", "router.py"), "w", encoding="utf-8") as f:
                f.write(ChipTemplates.get_router_template(spec))
            # Also create __init__.py
            open(os.path.join(chip_folder, "core", "__init__.py"), "a").close()

        logger.info(f"Chip {spec.slug} installed at {chip_folder}")
        return chip_folder

    def uninstall(self, slug: str, target_root: str = "chips/"):
        chip_folder = os.path.join(target_root, f"chip-{slug}")
        if os.path.exists(chip_folder):
            shutil.rmtree(chip_folder)
            logger.info(f"Chip {slug} uninstalled.")
