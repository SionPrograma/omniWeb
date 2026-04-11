import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def test_root():
    try:
        res = requests.get(f"{BASE_URL}/")
        print(f"ROOT: {res.status_code}")
        return res.status_code == 200
    except Exception as e:
        print(f"ROOT: ERROR {e}")
        return False

def test_health():
    try:
        res = requests.get(f"{BASE_URL}/api/v1/system/health")
        print(f"HEALTH: {res.status_code} - {res.text}")
        return res.status_code == 200
    except Exception as e:
        # Maybe endpoint doesn't exist
        print(f"HEALTH: FAILED/NOT FOUND {e}")
        return False

def test_state():
    try:
        res = requests.get(f"{BASE_URL}/api/v1/system/state")
        print(f"STATE: {res.status_code}")
        return res.status_code == 200
    except Exception as e:
        print(f"STATE: ERROR {e}")
        return False

if __name__ == "__main__":
    r = test_root()
    h = test_health()
    s = test_state()
    if r and s:
        print("BACKEND SMOKE: PASS")
        sys.exit(0)
    else:
        print("BACKEND SMOKE: FAIL")
        sys.exit(1)
