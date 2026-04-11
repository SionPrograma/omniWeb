import sys
import os
import logging
import asyncio

# Setup basic logging
logging.basicConfig(level=logging.INFO)

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context, enforce_permission, PermissionDeniedError
from backend.core.module_registry import module_registry
from fastapi import FastAPI

async def verify_phase_1_final():
    print("\n--- FINAL VERIFICATION PHASE 1 ---")
    app = FastAPI()
    
    # Register chip
    module_registry.register_module(app, "finanzas", "chips.chip-finanzas.core.router")
    
    with set_chip_context("finanzas"):
        # 1. Check authorized permission
        print("\nTest 1: 'db_access' (Present in metadata)...")
        try:
            enforce_permission("db_access")
            print("  SUCCESS: Authorized correctly.")
        except PermissionDeniedError:
            print("  FAILED: Denied authorized permission.")

        # 2. Check unauthorized permission
        print("\nTest 2: 'system_patch_access' (Missing in metadata)...")
        try:
            enforce_permission("system_patch_access")
            print("  FAILED: Bypassed security! Permission allowed when not in metadata.")
        except PermissionDeniedError:
            print("  SUCCESS: Denied as expected. No bypass introduced.")

if __name__ == "__main__":
    asyncio.run(verify_phase_1_final())
