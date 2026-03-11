import requests
import sys

BASE_URL = "http://127.0.0.1:8000" # Default port
ADMIN_TOKEN = "omniweb-dev-secret-token" # From config.py default

def audit_health():
    print("Audit: Checking System Health...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/system/health")
        if r.status_code == 200 and r.json().get("status") == "ok":
            print("   [PASS] Health endpoint active.")
        else:
            print(f"   [FAIL] Health endpoint returned {r.status_code}: {r.text}")
    except Exception as e:
        print(f"   [FAIL] Health check failed: {e}")

def audit_stats():
    print("\nAudit: Checking System Stats...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/system/stats")
        if r.status_code == 200:
            print(f"   [PASS] Stats active: {r.json()}")
        else:
            print(f"   [FAIL] Stats endpoint returned {r.status_code}")
    except Exception as e:
        print(f"   [FAIL] Stats check failed: {e}")

def audit_auth_protection():
    print("\nAudit: Verifying Auth Protection on Backup...")
    try:
        # Without token
        r = requests.post(f"{BASE_URL}/api/v1/system/db/backup")
        if r.status_code == 401:
            print("   [PASS] Backup correctly guarded by 401 (Unauthorized).")
        else:
            print(f"   [FAIL] Backup returned {r.status_code} without token.")
            
        # With token
        headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        r = requests.post(f"{BASE_URL}/api/v1/system/db/backup", headers=headers)
        if r.status_code == 200:
            print("   [PASS] Backup succeeded with valid token.")
        else:
            print(f"   [FAIL] Backup failed even with token: {r.status_code} - {r.text}")
    except Exception as e:
        print(f"   [FAIL] Auth audit failed: {e}")

def audit_chip_discovery():
    print("\nAudit: Checking Chip Discovery (OS Admin check)...")
    try:
        r = requests.get(f"{BASE_URL}/api/v1/system/chips")
        chips = r.json()
        slugs = [c["slug"] for c in chips]
        print(f"   Discovered chips: {slugs}")
        if "os-admin" in slugs:
             # Should be hidden from dashboard_visible, but maybe present in API?
             # Let's check dashboard_visible filtering
             pass
        
        # os-admin has dashboard_visible: false in chip.json
        for chip in chips:
            if chip["slug"] == "os-admin":
                print("   [FAIL] os-admin should be hidden from public API List (dashboard_visible: false)")
                return
        print("   [PASS] os-admin is hidden from public API List.")
    except Exception as e:
        print(f"   [FAIL] Chip discovery audit failed: {e}")

def audit_ai_host():
    print("\nAudit: Checking AI Host Orchestration (as Anonymous)...")
    try:
        r = requests.post(f"{BASE_URL}/api/v1/ai-host/process", json={"message": "hello"})
        if r.status_code == 401:
            print("   [PASS] AI Host correctly guarded by 401.")
        else:
            print(f"   [FAIL] AI Host returned {r.status_code} without token.")

        print("Audit: Checking AI Host Orquestration (as Admin)...")
        headers = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
        r = requests.post(f"{BASE_URL}/api/v1/ai-host/process", 
                          json={"message": "abrir finanzas"}, 
                          headers=headers)
        if r.status_code == 200:
            print(f"   [PASS] AI Host processed command: {r.json().get('message')}")
        else:
            print(f"   [FAIL] AI Host failed with token: {r.status_code}")
    except Exception as e:
        print(f"   [FAIL] AI Host audit failed: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        BASE_URL = sys.argv[1]
    
    print(f"--- STARTING OMNIWEB REALITY AUDIT ON {BASE_URL} ---")
    audit_health()
    audit_stats()
    audit_auth_protection()
    audit_chip_discovery()
    audit_ai_host()
    print("\n--- AUDIT COMPLETE ---")
