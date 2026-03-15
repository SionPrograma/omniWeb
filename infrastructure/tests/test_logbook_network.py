import pytest
import requests
import time
import uuid

BASE_URL = "http://127.0.0.1:8000/api/v1"

def test_logbook_flow():
    user_a = f"user_a_{uuid.uuid4().hex[:6]}"
    user_b = f"user_b_{uuid.uuid4().hex[:6]}"
    
    # 1. Create entry for User A
    resp = requests.post(f"{BASE_URL}/logbook/entries", json={
        "user_id": user_a,
        "type": "idea",
        "content": "Exploring quantum computing and space exploration",
        "tags": ["quantum", "space"]
    })
    assert resp.status_code == 200
    
    # 2. Create entry for User B (matching topic)
    requests.post(f"{BASE_URL}/logbook/entries", json={
        "user_id": user_b,
        "type": "project",
        "content": "Building a space telescope using quantum sensors",
        "tags": ["space", "quantum"]
    })
    
    # 3. Check affinity for User A
    resp = requests.get(f"{BASE_URL}/logbook/affinity?user_id={user_a}")
    assert resp.status_code == 200
    suggestions = resp.json().get("suggestions", [])
    assert len(suggestions) > 0
    assert any(s["matching_topics"] and "space" in s["matching_topics"] for s in suggestions)
    
    target_id = suggestions[0]["target_logbook_id"]
    
    # 4. Connect
    resp = requests.post(f"{BASE_URL}/logbook/connect", json={
        "user_id": user_a,
        "target_user_id": user_b,
        "type": "collaboration"
    })
    assert resp.status_code == 200
    
    # 5. Verify connection in Logbook
    resp = requests.get(f"{BASE_URL}/logbook/me?user_id={user_a}")
    logbook = resp.json()
    assert any(c["target_logbook_id"] == target_id for c in logbook["connections"])

if __name__ == "__main__":
    try:
        test_logbook_flow()
        print("Logbook Network Test: PASS")
    except Exception as e:
        import traceback
        traceback.print_exc()
        print(f"Logbook Network Test: FAIL - {e}")
