import requests
import time
import subprocess
import json

def test_permissions():
    print("Starting server...")
    proc = subprocess.Popen(["uvicorn", "backend.main:app", "--port", "8001"])
    time.sleep(3) # Wait for server to start
    
    try:
        # Test 1: System Chips endpoint (Dashboard visibility)
        print("Testing /api/v1/system/chips...")
        resp = requests.get("http://localhost:8001/api/v1/system/chips")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        chips = resp.json()
        print(f"Loaded {len(chips)} chips successfully.")
        
        # Test 2: Finanzas API (requires DB access and event subscribe) 
        # By calling the finanzas backend, we will verify if db_manager.get_connection() raises PermissionDeniedError or works
        # Let's hit the finanzas /api/v1/finanzas/health or /api/v1/finanzas/transactions
        print("Testing /api/v1/finanzas/transactions (DB Access test)...")
        resp = requests.get("http://localhost:8001/api/v1/finanzas/transactions")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("Finanzas DB access works correctly.")
        
        # Test 3: Reparto API (requires DB access and event publish)
        print("Testing /api/v1/reparto/stops (DB Access test)...")
        resp = requests.get("http://localhost:8001/api/v1/reparto/stops")
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        print("Reparto DB access works correctly.")
        
        # We can't easily test a chip failing unless we modify its metadata temporarily.
        # But for now, ensuring we didn't break the existing modules is the validation.
        print("All tests passed successfully.")
        
    finally:
        print("Shutting down server...")
        proc.terminate()
        proc.wait()

if __name__ == "__main__":
    test_permissions()
