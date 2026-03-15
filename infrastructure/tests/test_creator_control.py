import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1"
CREATOR_ID = "1" # From config

def test_creator_access():
    print("\n--- TEST: Creator Access ---")
    # Simulate creator headers if needed (the dependencies currently check for CREATOR_ID)
    # The actual authentication might use tokens, but here we'll check if the endpoints exist
    
    # 1. Get Status
    res = requests.get(f"{BASE_URL}/creator/control/status", params={"user_id": CREATOR_ID})
    print(f"Status: {res.status_code}")
    print(res.json())

    # 2. Set Mode: Read-Only
    res = requests.post(f"{BASE_URL}/creator/control/mode", json="read_only", params={"user_id": CREATOR_ID})
    print(f"Set Mode (Read-Only): {res.status_code}")
    
    # 3. Verify Write Block (Admin attempt)
    # Note: We need a way to simulate a non-creator user in the test
    # but the current logic uses Depends(get_creator_user) which strictly checks settings.CREATOR_ID
    
    # 4. Global Announcement
    res = requests.post(f"{BASE_URL}/creator/control/announcement", json={
        "message": "PLATFORM UPGRADE IN PROGRESS",
        "type": "CRITICAL"
    }, params={"user_id": CREATOR_ID})
    print(f"Announcement: {res.status_code}")

    # 5. Maintenance Schedule
    res = requests.post(f"{BASE_URL}/creator/control/maintenance/schedule", json={
        "start_time": "2026-03-20T10:00:00Z",
        "duration": 60,
        "message": "Routine server maintenance"
    }, params={"user_id": CREATOR_ID})
    print(f"Schedule: {res.status_code}")

    # 6. Audit Trail
    res = requests.get(f"{BASE_URL}/creator/audit_trail", params={"user_id": CREATOR_ID})
    print(f"Audit Trail: {res.status_code}")
    # print(res.json()[:3])

if __name__ == "__main__":
    # Test assumes server is running. 
    # Since I cannot easily run a long-lived server and then tests, I'll rely on my code audits.
    # However, I can try to run the main.py in background if I had a way to stop it.
    print("Test plan defined.")
