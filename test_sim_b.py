import os
import sys
import json
import shutil
from fastapi import FastAPI

# Define paths
CHIPS_DIR = "chips"
SIM_B_PATH = os.path.join(CHIPS_DIR, "chip-sim_import_error")

def setup_sim_b():
    os.makedirs(os.path.join(SIM_B_PATH, "core"), exist_ok=True)
    with open(os.path.join(SIM_B_PATH, "chip.json"), "w") as f:
        json.dump({
            "id": "chip-sim_import_error",
            "slug": "sim_import_error",
            "name": "Sim Import Error",
            "has_backend": True,
            "active": True
        }, f)
    with open(os.path.join(SIM_B_PATH, "core", "router.py"), "w") as f:
        f.write("raise Exception('CRITICAL_SIMULATED_IMPORT_ERROR')")

def cleanup_sim_b():
    if os.path.exists(SIM_B_PATH): shutil.rmtree(SIM_B_PATH)

def test_registration_hardening():
    sys.path.append(os.getcwd())
    from backend.core.config import settings
    from backend.core.module_registry import module_registry
    app = FastAPI()
    
    # Simulate main.py logic for Sim B
    module_name = "sim_import_error"
    chip_metadata = {"slug": "sim_import_error", "has_backend": True, "active": True}
    router_path = "chips.chip-sim_import_error.core.router"
    
    print(f"Attempting to register {module_name}...")
    try:
        module_registry.register_module(
            app=app,
            module_name=module_name,
            router_import_path=router_path,
            prefix=f"/api/v1/{module_name}"
        )
    except Exception as e:
        print(f"Caught expected error: {e}")
    
    # Check if registered
    if module_name in module_registry.modules:
        print(f"RESULT: {module_name} reached registry. Prefix: {module_registry.modules[module_name]['prefix']}")
    else:
        print(f"RESULT: {module_name} MISSING from registry. (Structural Risk identified)")

def test_reparto_perms():
    sys.path.append(os.getcwd())
    print("\nVerifying chip-reparto startup...")
    # This will trigger repository initialization which performs DB check
    try:
        from backend.core.permissions import set_chip_context
        with set_chip_context("reparto"):
            from chips.chip_reparto.core.router import router
            print("SUCCESS: chip-reparto imported without permission denial.")
    except Exception as e:
        print(f"FAIL: chip-reparto failed: {e}")

if __name__ == "__main__":
    try:
        setup_sim_b()
        test_registration_hardening()
        test_reparto_perms()
    finally:
        cleanup_sim_b()
