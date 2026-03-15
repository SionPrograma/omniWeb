import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/system/cluster"
CREATOR_ID = "1"

def test_offline_mode():
    print("--- PHASE 27 TEST: OFFLINE AUTONOMOUS MODE ---")
    
    # 1. Check current status
    res = requests.get(f"{BASE_URL}/offline/state", params={"user_id": CREATOR_ID})
    state = res.json()
    print(f"Initial State: Offline={state['is_offline']}, Backlog={state['backlog_count']}")

    # 2. Simulate task submission in autonomous mode
    # (Note: In a real test we would disconnect the mesh, here we test the router fallback)
    # We submit a task and if the router detects "offline" (simulated in manager), it buffers it.
    
    # 3. Verify backlog inclusion
    # We call the submission endpoint
    res = requests.post(f"{BASE_URL}/task/submit", params={"user_id": CREATOR_ID, "chip_slug": "core"}, json={})
    print(f"Task submitted: {res.status_code}")
    
    # 4. Check backlog again
    res = requests.get(f"{BASE_URL}/offline/state", params={"user_id": CREATOR_ID})
    state = res.json()
    print(f"State after Task: Offline={state['is_offline']}, Backlog={state['backlog_count']}")

if __name__ == "__main__":
    print("Offline test script ready.")
    # test_offline_mode()
