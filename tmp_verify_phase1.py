import sys
import os
import logging
import asyncio
import importlib

# Setup basic logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context
from backend.core.module_registry import module_registry
from fastapi import FastAPI

async def verify_phase_1_async():
    print("\n--- VERIFYING PHASE 1: Safe Backend Naturalization ---")
    
    app = FastAPI()
    
    # 1. Initialize Core
    with set_chip_context("core"):
        db_manager.init_db()
    
    # 2. Registration Phase
    print("\nStage 1: Registering chip-finanzas...")
    # Using the exact path used by the system
    success = module_registry.register_module(app, "finanzas", "chips.chip-finanzas.core.router")
    
    print(f"Registration success: {success}")
    
    chip_info = module_registry.modules.get("finanzas")
    if chip_info:
        print(f"Chip Status in Registry: {chip_info.get('status')}")
        print(f"Active Backend: {chip_info.get('active_backend')}")
        # DEBUG: Check metadata
        # print(f"Chip Metadata keys: {chip_info.get('metadata', {}).keys()}")
        # print(f"Chip Permissions: {chip_info.get('metadata', {}).get('permissions')}")
    else:
        print("FAILED: Chip 'finanzas' not found in registry.")
        return

    # 3. Functional Execution Phase
    print("\nStage 2: Testing Router Directly (Triggering Lazy Init)...")
    try:
        # Direct import of hyphenated path requires importlib
        mod = importlib.import_module("chips.chip-finanzas.core.router")
        list_transactions = getattr(mod, "list_transactions")
        
        with set_chip_context("finanzas"):
            # Calling the router function directly
            result = await list_transactions()
            print(f"SUCCESS: Router function returned {len(result)} records.")
            if len(result) > 0:
                print(f"Sample Data: {result[0]}")
    except Exception as e:
        print(f"CRITICAL ERROR during execution: {e}")
        # import traceback
        # traceback.print_exc()

    # 4. Verification of Permissions
    print("\nStage 3: Verifying Permission Enforcement...")
    with set_chip_context("finanzas"):
        try:
            db_manager.get_connection()
            print("Verified: 'finanzas' can access DB (Permission enforced via registry).")
        except Exception as e:
            print(f"FAILED: 'finanzas' could not access DB despite metadata: {e}")
            # print(f"Registry Content for finanzas: {module_registry.modules.get('finanzas')}")

if __name__ == "__main__":
    asyncio.run(verify_phase_1_async())
