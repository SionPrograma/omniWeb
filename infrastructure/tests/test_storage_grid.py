import requests
import json

BASE_URL = "http://localhost:8000/api/v1/system/cluster"
CREATOR_ID = "1"

def test_storage_grid():
    print("--- PHASE 29 TEST: DISTRIBUTED STORAGE GRID ---")
    
    # 1. Check Initial Grid State
    res = requests.get(f"{BASE_URL}/storage/state", params={"user_id": CREATOR_ID})
    state = res.json()
    print(f"Initial Storage: {state['used_capacity']} bytes used.")

    # 2. Simulate Storage Manager Usage (Direct DB check or through future internal API)
    # Since we don't have a public POST /storage/upload yet (it's internal for components),
    # we just verify the state endpoint returns the expected model.
    print(f"Capacity: {state['total_capacity'] / (1024**3):.1f} GB")
    print(f"Replication Factor: {state['replication_factor']}x")

if __name__ == "__main__":
    print("Storage Grid test script ready.")
    # test_storage_grid()
