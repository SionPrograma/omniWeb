import os
import sys
import json
import shutil
from fastapi import FastAPI

# Define paths
CHIPS_DIR = "chips"
SIM_C_PATH = os.path.join(CHIPS_DIR, "chip-sim_dep_error")

def setup_sim_c():
    os.makedirs(os.path.join(SIM_C_PATH, "core"), exist_ok=True)
    with open(os.path.join(SIM_C_PATH, "chip.json"), "w") as f:
        json.dump({
            "id": "chip-sim_dep_error",
            "slug": "sim_dep_error",
            "name": "Sim Dep Error",
            "has_backend": True,
            "active": True
        }, f)
    # Raising an ImportError that looks like a dependency
    with open(os.path.join(SIM_C_PATH, "core", "router.py"), "w") as f:
        f.write("import non_existent_library_omni_test")

def cleanup_sim_c():
    if os.path.exists(SIM_C_PATH): shutil.rmtree(SIM_C_PATH)

def test_registration_hardening_dep():
    sys.path.append(os.getcwd())
    from backend.core.config import settings
    from backend.core.module_registry import module_registry
    app = FastAPI()
    
    module_name = "sim_dep_error"
    chip_metadata = {"slug": "sim_dep_error", "has_backend": True, "active": True}
    router_path = "chips.chip-sim_dep_error.core.router"
    
    print(f"Attempting to register {module_name}...")
    try:
        module_registry.register_module(
            app=app,
            module_name=module_name,
            router_import_path=router_path,
            prefix=f"/api/v1/{module_name}"
        )
    except Exception as e:
        print(f"Caught expected CRITICAL error: {e}")
        # Mimic main.py patched except block
        module_registry._register_module_state(module_name, None, chip_metadata)
    
    # Check if registered
    if module_name in module_registry.modules:
        print(f"RESULT: {module_name} reached registry. Prefix: {module_registry.modules[module_name]['prefix']}")
    else:
        print(f"RESULT: {module_name} MISSING from registry.")

if __name__ == "__main__":
    try:
        setup_sim_c()
        test_registration_hardening_dep()
    finally:
        cleanup_sim_c()
