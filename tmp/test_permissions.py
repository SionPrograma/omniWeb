
import sys
import os

# Ensure backend is in path
sys.path.append('c:/Users/Propietario/Desktop/plan actual/07-proyectosGrandes/01-omniweb')

from backend.core.database import db_manager
from backend.core.permissions import set_chip_context, PermissionDeniedError

def test_permission_enforcement():
    print("Testing permission enforcement...")
    
    # 1. Access with 'core' (should work)
    with set_chip_context("core"):
        try:
            with db_manager.get_connection() as conn:
                conn.execute("SELECT 1")
            print("OK: 'core' granted DB access.")
        except PermissionDeniedError:
            print("FAIL: 'core' denied DB access.")
            
    # 2. Access with 'reparto' (has db_access in chip.json)
    with set_chip_context("reparto"):
        try:
            with db_manager.get_connection() as conn:
                conn.execute("SELECT 1")
            print("OK: 'reparto' granted DB access.")
        except PermissionDeniedError:
            print("FAIL: 'reparto' denied DB access.")
            
    # 3. Access with 'test-chip' (NO permission)
    with set_chip_context("test-chip"):
        try:
            with db_manager.get_connection() as conn:
                conn.execute("SELECT 1")
            print("FAIL: 'test-chip' granted DB access (expected denial).")
        except PermissionDeniedError:
            print("OK: 'test-chip' denied DB access.")
        except Exception as e:
            if "Chip 'test-chip' inactivo o no registrado" in str(e):
                print("OK: 'test-chip' denied DB access (not registered).")
            else:
                print(f"ERROR: Unexpected exception: {e}")

if __name__ == "__main__":
    test_permission_enforcement()
