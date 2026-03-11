import os
import json
from backend.core.module_registry import ChipMetadata

class ChipValidator:
    """
    Ensures a generated chip is safe and follows OmniWeb standards.
    """
    def validate(self, chip_dir: str) -> bool:
        # 1. Existence of chip.json
        json_path = os.path.join(chip_dir, "chip.json")
        if not os.path.exists(json_path):
            return False, "Missing chip.json"
            
        # 2. Schema validation
        try:
            with open(json_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                ChipMetadata(**data)
        except Exception as e:
            return False, f"Invalid chip.json schema: {e}"

        # 3. Slug check (folder name must match slug)
        slug = data.get("slug")
        if not slug or f"chip-{slug}" != os.path.basename(chip_dir):
            return False, "Slug / Folder mismatch"

        # 4. Critical Files
        if data.get("has_frontend"):
            if not os.path.exists(os.path.join(chip_dir, "frontend", "index.html")):
                return False, "Missing frontend/index.html"
                
        if data.get("has_backend"):
            if not os.path.exists(os.path.join(chip_dir, "core", "router.py")):
                return False, "Missing core/router.py"

        return True, "Success"
