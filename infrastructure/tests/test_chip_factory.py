import asyncio
import os
import sys
import shutil
sys.path.append(os.getcwd())
from backend.core.chip_factory.factory import chip_factory
from backend.core.module_registry import module_registry

async def test_chip_generation():
    print("\n--- Testing Chip Factory Generation ---")
    
    # Clean up if exists
    target_slug = "custom-notes"
    target_dir = f"chips/chip-{target_slug}"
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)

    # 1. Create chip
    result = await chip_factory.create_from_request("Crea un chip de notas para mis tareas")
    
    print(f"Result: {result}")
    
    # 2. Assertions
    assert result["status"] == "success"
    assert os.path.exists(target_dir)
    assert os.path.exists(os.path.join(target_dir, "chip.json"))
    assert os.path.exists(os.path.join(target_dir, "core", "router.py"))
    
    # 3. Discovery check
    all_chips = module_registry.discover_all_chips()
    found = any(c["slug"] == target_slug for c in all_chips)
    assert found == True
    print("   [PASS] Chip generated and discovered by system.")

    # 4. Cleanup
    shutil.rmtree(target_dir)
    print("   [CLEANUP] Test chip removed.")

if __name__ == "__main__":
    asyncio.run(test_chip_generation())
