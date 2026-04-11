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

async def verify_phase_2_async():
    print("\n--- VERIFYING PHASE 2: Blueprint Generalization ---")
    
    app = FastAPI()
    
    # 1. Initialize Core
    with set_chip_context("core"):
        db_manager.init_db()
    
    # 2. Dual Registration
    print("\nStage 1: Registering both Hybrid chips...")
    success_fin = module_registry.register_module(app, "finanzas", "chips.chip-finanzas.core.router")
    success_rep = module_registry.register_module(app, "reparto", "chips.chip-reparto.core.router")
    
    print(f"Finanzas Registration: {success_fin}")
    print(f"Reparto Registration: {success_rep}")
    
    for slug in ["finanzas", "reparto"]:
        info = module_registry.modules.get(slug)
        print(f"Chip '{slug}': Status={info.get('status')}, ActiveBackend={info.get('active_backend')}")

    # 3. Functional Execution - Finanzas (Regression check)
    print("\nStage 2: Checking Finanzas (Regression)...")
    try:
        mod_fin = importlib.import_module("chips.chip-finanzas.core.router")
        list_txs = getattr(mod_fin, "list_transactions")
        with set_chip_context("finanzas"):
            res = await list_txs()
            print(f"SUCCESS: Finanzas healthy. Records: {len(res)}")
    except Exception as e:
        print(f"FAILED: Finanzas regression: {e}")

    # 4. Functional Execution - Reparto (Blueprint validation)
    print("\nStage 3: Checking Reparto (Blueprint Validation)...")
    try:
        mod_rep = importlib.import_module("chips.chip-reparto.core.router")
        get_stops = getattr(mod_rep, "get_stops")
        with set_chip_context("reparto"):
            # Call 1: Triggers Lazy Init and Seeding
            res1 = await get_stops()
            count1 = len(res1["stops"])
            print(f"SUCCESS: Reparto activated. Seed records: {count1}")
            
            # Call 2: Check for Duplication
            res2 = await get_stops()
            count2 = len(res2["stops"])
            print(f"SUCCESS: Second call records: {count2}")
            
            if count1 == count2:
                print("SUCCESS: No seed duplication detected.")
            else:
                print(f"FAILED: Seed duplication! {count1} -> {count2}")
                
    except Exception as e:
        print(f"FAILED: Reparto activation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(verify_phase_2_async())
