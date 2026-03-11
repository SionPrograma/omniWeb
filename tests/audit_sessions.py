import requests
import sys

BASE_URL = "http://127.0.0.1:8000"

def audit_session_flow():
    print("--- AUDITING USER SESSION FLOW ---")
    
    # 1. Login with Admin (from DB seed)
    print("Audit: Performing DB-backed Login...")
    payload = {"username": "admin", "password": "admin"}
    r = requests.post(f"{BASE_URL}/api/v1/auth/token", data=payload)
    
    if r.status_code == 200:
        token = r.json().get("access_token")
        print(f"   [PASS] Login successful. Token: {token[:10]}...")
    else:
        print(f"   [FAIL] Login failed: {r.status_code} - {r.text}")
        return

    # 2. Verify /auth/me
    print("\nAudit: Verifying /auth/me profile...")
    headers = {"Authorization": f"Bearer {token}"}
    r = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    if r.status_code == 200:
        print(f"   [PASS] Profile profile: {r.json()}")
    else:
        print(f"   [FAIL] Failed to fetch profile: {r.status_code}")

    # 3. Test Logout
    print("\nAudit: Verifying Logout...")
    r = requests.post(f"{BASE_URL}/api/v1/auth/logout", headers=headers)
    if r.status_code == 200:
        print("   [PASS] Logout successful.")
    else:
        print(f"   [FAIL] Logout failed: {r.status_code}")

    # 4. Verify Token is Inactive
    print("\nAudit: Verifying token inaccessibility after logout...")
    r = requests.get(f"{BASE_URL}/api/v1/auth/me", headers=headers)
    if r.status_code == 401:
        print("   [PASS] Token correctly invalidated.")
    else:
        print(f"   [FAIL] Profile still accessible after logout: {r.status_code}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    audit_session_flow()
