import os
import sys
import json
import shutil
import importlib
import logging

# Define paths
CHIPS_DIR = "chips"
SIM_A_PATH = os.path.join(CHIPS_DIR, "chip-sim_no_router")
SIM_B_PATH = os.path.join(CHIPS_DIR, "chip-sim_import_error")

def setup_simulations():
    print("Setting up simulation chips...")
    # Sim A: has_backend=True, no router file
    os.makedirs(SIM_A_PATH, exist_ok=True)
    with open(os.path.join(SIM_A_PATH, "chip.json"), "w") as f:
        json.dump({
            "id": "chip-sim_no_router",
            "slug": "sim_no_router",
            "name": "Sim No Router",
            "has_backend": True,
            "active": True
        }, f)
    
    # Sim B: has_backend=True, router file with import error
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

def cleanup_simulations():
    print("Cleaning up simulation chips...")
    if os.path.exists(SIM_A_PATH): shutil.rmtree(SIM_A_PATH)
    if os.path.exists(SIM_B_PATH): shutil.rmtree(SIM_B_PATH)

def run_audit():
    sys.path.append(os.getcwd())
    
    # Import settings to configure logging and paths
    from backend.core.config import settings
    from backend.core.module_registry import module_registry
    from fastapi import FastAPI
    
    app = FastAPI()
    
    print("\n--- STARTING RUNTIME AUDIT ---")
    
    # 1. Discover all chips
    chips_meta = module_registry.discover_all_chips()
    print(f"Discovered {len(chips_meta)} chips on disk.")
    
    # 2. Simulate the loop in main.py
    for chip_metadata in chips_meta:
        module_name = chip_metadata["slug"]
        if not chip_metadata.get("active", True):
            continue
            
        print(f"Processing chip: {module_name}")
        
        possible_routers = [
            (f"chips/chip-{module_name}/core/router.py", f"chips.chip-{module_name}.core.router"),
            (f"chips/chip-{module_name}/backend/router.py", f"chips.chip-{module_name}.backend.router")
        ]
        
        found_import_path = None
        for file_path, import_path in possible_routers:
            if os.path.exists(file_path):
                found_import_path = import_path
                break
        
        if found_import_path:
            try:
                module_registry.register_module(
                    app=app,
                    module_name=module_name,
                    router_import_path=found_import_path,
                    prefix=f"/api/v1/{module_name}"
                )
            except Exception as e:
                print(f"ISOLATED FAILURE: Chip '{module_name}' failed to register: {e}")
        elif chip_metadata.get("has_backend"):
            module_registry._register_module_state(module_name, None, chip_metadata)
            print(f"WARNING: Chip '{module_name}' claims backend but no router found (Graceful state recorded).")

    # 3. Verify module registry state
    print("\nRegistry Verification:")
    modules = module_registry.modules
    
    # Check reparto
    if "reparto" in modules:
        print(f"SUCCESS: 'reparto' registered. Status: {modules['reparto']['status']}")
    else:
        print("FAIL: 'reparto' not in registry.")
        
    # Check Sim A
    if "sim_no_router" in modules:
        print(f"SUCCESS: 'sim_no_router' registered. Prefix: {modules['sim_no_router']['prefix']} (Expect None)")
    else:
        print("FAIL: 'sim_no_router' not in registry.")
        
    # Check Sim B
    if "sim_import_error" in modules:
        print(f"SUCCESS: 'sim_import_error' registered. Prefix: {modules['sim_import_error']['prefix']} (Expect None due to error isolation)")
    else:
        print("FAIL: 'sim_import_error' not in registry (Wait, should it be there? register_module might not call _register_module_state if it raises before that).")
        # Let's check the code: register_module calls _discover_backend_router first.
        # If _discover_backend_router returns None, it calls _register_module_state.
        # BUT if router.py raises Exception, _discover_backend_router catches it (lines 103-107 and 132-133)?
        # No, Strategy A re-raises if it's not ModuleNotFoundError or AttributeError (Line 107).
        # So register_module will raise the exception.
        # BUT our loop in main.py catches it!
        # HOWEVER, the loop in main.py DOES NOT call _register_module_state in the except block.
        # THIS IS A FINDING.

    # 4. Verify consumers
    print("\nConsumer Verification (SystemStateEngine):")
    from backend.core.system_state.engine import state_engine
    # Mocking what state engine does
    all_chips = module_registry.discover_all_chips()
    for c in all_chips:
        slug = c.get("slug")
        reg_info = modules.get(slug)
        # Check if any consumer would crash
        status = "active" if c.get("active") else "disabled"
        # Prefix check
        prefix = reg_info.get("prefix") if reg_info else "not_registered"
        print(f" - {slug}: Status={status}, RegistryPrefix={prefix}")

if __name__ == "__main__":
    try:
        setup_simulations()
        run_audit()
    finally:
        cleanup_simulations()
