import sys
import os
import logging

# Setup basic logging to see our results
logging.basicConfig(level=logging.INFO)

# Ensure project root is in path
sys.path.append(os.getcwd())

from backend.core.database import db_manager
from backend.core.permissions import _log_denial, set_chip_context

def verify_phase_0():
    print("\n--- VERIFYING PHASE 0 ---")
    
    # 1. Test Identity Seeding
    print("\nStep 1: Running Identity Seeding...")
    with set_chip_context("core"):
        db_manager.init_db()
    
    # Check if user exists
    import sqlite3
    conn = sqlite3.connect('backend/data/omniweb.db')
    conn.row_factory = sqlite3.Row
    user = conn.execute("SELECT * FROM users WHERE id = '00000000-0000-0000-0000-000000000000'").fetchone()
    if user:
        print(f"SUCCESS: System User (id={user['id']}) verified in DB.")
    else:
        print("FAILED: System User not found.")
    conn.close()

    # 2. Test Logger Hardening (Trigger Denial)
    print("\nStep 2: Testing Logger Hardening (Triggering Denial)...")
    try:
        # Triggering a denial for a mock chip
        _log_denial("mock-chip", None, "db_access")
        print("SUCCESS: _log_denial executed without crashing.")
    except Exception as e:
        print(f"FAILED: _log_denial crashed with: {e}")

    # 3. Test Module Registry Degradation
    print("\nStep 3: Testing Module Registry Degradation...")
    from backend.core.module_registry import module_registry
    from fastapi import FastAPI
    app = FastAPI()
    
    # We know chip-finanzas fails due to import-time DB access
    print("Attempting to register chip-finanzas...")
    success = module_registry.register_module(app, "finanzas", "chips.chip-finanzas.core.router")
    
    chip_info = module_registry.modules.get("finanzas")
    if chip_info:
        print(f"Chip Info Status: {chip_info.get('status')}")
        print(f"Backend Active: {chip_info.get('active_backend')}")
        if chip_info.get('status') == 'damaged_backend':
            print("SUCCESS: Chip degraded safely to damaged_backend.")
        else:
            print(f"NOTE: Chip status is {chip_info.get('status')}")
    else:
        print("FAILED: Chip not registered at all.")

if __name__ == "__main__":
    verify_phase_0()
