
import requests

BASE_URL = "http://localhost:8000/api/v1"
ADMIN_TOKEN = "omniweb-dev-secret-token"
HEADERS = {"Authorization": f"Bearer {ADMIN_TOKEN}"}

def validate_recovery():
    print("=== STARTING RUNTIME RECOVERY VALIDATION ===")
    
    # 1. Health check (via a simple GET)
    try:
        res = requests.get(f"{BASE_URL}/governance/stats", headers=HEADERS)
        print(f"Stats check: {res.status_code} - {res.json().get('status')}")
    except Exception as e:
        print(f"Stats check failed: {e}")

    # 2. Catalyst Traces (Recent touched area)
    try:
        res = requests.get(f"{BASE_URL}/governance/catalyst/traces", headers=HEADERS)
        print(f"Catalyst Traces: {res.status_code} - Found {len(res.json().get('payload', []))} traces.")
    except Exception as e:
        print(f"Catalyst traces failed: {e}")

    # 3. Wisdom Atlas Node (Recent touched area)
    try:
        res = requests.get(f"{BASE_URL}/governance/wisdom/atlas/node/WNODE-TEST-001", headers=HEADERS)
        print(f"Atlas Node: {res.status_code} - {res.json().get('status')}")
    except Exception as e:
        print(f"Atlas node failed: {e}")

    print("=== VALIDATION FINISHED ===")

if __name__ == "__main__":
    validate_recovery()
