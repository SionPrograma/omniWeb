import sys
import os
import importlib
from fastapi import APIRouter

# Replicate standard sys.path setup
sys.path.append(os.getcwd())

def test_reparto_import():
    from backend.core.permissions import set_chip_context, _current_ctx_info
    
    print("Testing reparto import with context...")
    module_name = "reparto"
    router_import_path = "chips.chip-reparto.core.router"
    
    with set_chip_context(module_name):
        ctx_before = _current_ctx_info.get()
        print(f"Context before import: {ctx_before}")
        try:
            module = importlib.import_module(router_import_path)
            print("Import successful!")
        except Exception as e:
            print(f"Import FAILED: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_reparto_import()
