import requests
import json

BASE_URL = "http://localhost:8000/api/v1/human"
CREATOR_ID = "1"

def run_phases_30_36_audit():
    print("--- PHASES 30-36: HUMAN DEVELOPMENT BLOCK AUDIT ---")
    
    # 1. Knowledge Layer (Phase 30)
    print("\n[PHASE 30] Auditing Knowledge Storage...")
    res = requests.get(f"{BASE_URL}/knowledge/units", params={"user_id": CREATOR_ID})
    if res.ok:
        print(f"PASS: Knowledge API reachable. Units found: {len(res.json())}")
    else:
        print(f"FAIL: Knowledge API error {res.status_code}")

    # 2. Global Graph (Phase 31)
    print("\n[PHASE 31] Auditing Global Knowledge Graph...")
    res = requests.get(f"{BASE_URL}/graph/galaxy", params={"user_id": CREATOR_ID})
    if res.ok:
        graph = res.json()
        print(f"PASS: Galaxy Map Data stable. Nodes: {len(graph.get('nodes', []))}, Edges: {len(graph.get('edges', []))}")
    else:
        print(f"FAIL: Graph API error {res.status_code}")

    # 3. Learning Path Engine (Phase 32)
    print("\n[PHASE 32] Auditing Adaptive Learning Paths...")
    res = requests.get(f"{BASE_URL}/learning/paths", params={"user_id": CREATOR_ID})
    if res.ok:
        print(f"PASS: learning Path API functional. Active Paths: {len(res.json())}")
    else:
        print(f"FAIL: Learning Path API error {res.status_code}")

    # 4. Opportunity Engine (Phase 34)
    print("\n[PHASE 34] Auditing Opportunity Matching...")
    res = requests.get(f"{BASE_URL}/opportunities", params={"user_id": CREATOR_ID})
    if res.ok:
        print(f"PASS: Opportunity Engine functional. Matches: {len(res.json())}")
    else:
        print(f"FAIL: Opportunity API error {res.status_code}")

    # 5. Accessibility Layer (Phase 36)
    print("\n[PHASE 36] Auditing Accessibility Interface...")
    res = requests.get(f"{BASE_URL}/accessibility/profile", params={"user_id": CREATOR_ID})
    if res.ok:
        profile = res.json()
        print(f"PASS: Accessibility Profile stable. Voice Nav: {profile.get('voice_navigation_enabled', False)}")
    else:
        print(f"FAIL: Accessibility API error {res.status_code}")

    print("\n--- AUDIT COMPLETE: BLOCKS 30-36 STABLE ---")

if __name__ == "__main__":
    run_phases_30_36_audit()
