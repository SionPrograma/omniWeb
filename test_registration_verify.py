import os
import sys

# Mock settings and module_registry
class MockSettings:
    API_V1_STR = "/api/v1"

settings = MockSettings()

# We'll use the real module_registry but mock the 'app'
from backend.core.module_registry import module_registry
from fastapi import FastAPI

app = FastAPI()

def simulate_startup():
    all_chips = module_registry.discover_all_chips()
    results = []
    for chip_metadata in all_chips:
        module_name = chip_metadata["slug"]
        
        possible_routers = [
            (f"chips/chip-{module_name}/core/router.py", f"chips.chip-{module_name}.core.router"),
            (f"chips/chip-{module_name}/backend/router.py", f"chips.chip-{module_name}.backend.router")
        ]
        
        found_path = None
        for file_path, import_path in possible_routers:
            if os.path.exists(file_path):
                found_path = import_path
                break
        
        if found_path:
            try:
                success = module_registry.register_module(
                    app=app,
                    module_name=module_name,
                    router_import_path=found_path,
                    prefix=f"{settings.API_V1_STR}/{module_name}"
                )
                results.append((module_name, "REGISTERED" if success else "FAILED"))
            except Exception as e:
                results.append((module_name, f"ERROR: {e}"))
        else:
            if chip_metadata.get("has_backend"):
                results.append((module_name, "NO_ROUTER_FOUND"))
            else:
                results.append((module_name, "FRONTEND_ONLY"))
                
    return results

if __name__ == "__main__":
    sys.path.append(os.getcwd())
    results = simulate_startup()
    for name, status in results:
        print(f"Chip {name}: {status}")
