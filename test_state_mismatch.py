import os
import sys
import json
import shutil
import asyncio

# Setup simulation for a "broken" chip
CHIPS_DIR = "chips"
BROKEN_CHIP_DIR = os.path.join(CHIPS_DIR, "chip-broken_test")

def setup_broken_chip():
    os.makedirs(os.path.join(BROKEN_CHIP_DIR, "core"), exist_ok=True)
    with open(os.path.join(BROKEN_CHIP_DIR, "chip.json"), "w") as f:
        json.dump({
            "id": "chip-broken_test",
            "slug": "broken_test",
            "name": "Broken Test Chip",
            "has_backend": True,
            "active": True
        }, f)
    with open(os.path.join(BROKEN_CHIP_DIR, "core", "router.py"), "w") as f:
        f.write("raise SyntaxError('Simulated Syntax Error')")

def cleanup_broken_chip():
    if os.path.exists(BROKEN_CHIP_DIR): shutil.rmtree(BROKEN_CHIP_DIR)

async def test_mismatch():
    sys.path.append(os.getcwd())
    from backend.core.module_registry import module_registry
    from backend.core.system_state.engine import state_engine
    from fastapi import FastAPI
    
    app = FastAPI()
    
    print("\n--- SIMULATING BACKEND STARTUP ---")
    module_name = "broken_test"
    chip_metadata = {"slug": module_name, "has_backend": True, "active": True}
    
    # 1. Simulate main.py behavior when a chip fails critically
    print(f"Attempting to register {module_name}...")
    try:
        # This will fail
        module_registry.register_module(app, module_name, f"chips.chip-{module_name}.core.router")
    except Exception as e:
        print(f"Caught registration error: {e}")
        # Patch from previous turn: register inactive state
        module_registry._register_module_state(module_name, None, chip_metadata)
    
    # 2. Inspect SystemStateEngine output
    print("\n--- INSPECTING SYSTEM STATE ---")
    from backend.core.permissions import set_chip_context
    with set_chip_context("core"):
        state = await state_engine.get_state(force_refresh=True)
    
    broken_chip = next((c for c in state.chips if c.slug == "broken_test"), None)
    if broken_chip:
        print(f"Chip: {broken_chip.slug}")
        print(f"Status in StateEngine: {broken_chip.status}")
        print(f"Health in StateEngine: {broken_chip.health}")
        
        # Check if matched with registry
        reg_info = module_registry.get_module_data("broken_test")
        print(f"Status in Registry: {reg_info['status'] if reg_info else 'Not Found'}")
        
        if broken_chip.health == "healthy" and reg_info.get("prefix") is None:
             print("\nMISMATCH DETECTED: Chip is reported as healthy but has no registered prefix.")
    else:
        print("FAIL: Chip not found in state.")

if __name__ == "__main__":
    try:
        setup_broken_chip()
        asyncio.run(test_mismatch())
    finally:
        cleanup_broken_chip()
