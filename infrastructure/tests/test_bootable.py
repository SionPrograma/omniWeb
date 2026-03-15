import requests
import json
import os

BASE_URL = "http://localhost:8000/api/v1/system"
CREATOR_ID = "1"

def test_bootable_runtime():
    print("--- PHASE 28 TEST: BOOTABLE RUNTIME ---")
    
    # 1. Verify Runtime State
    res = requests.get(f"{BASE_URL}/runtime", params={"user_id": CREATOR_ID})
    data = res.json()["runtime"]
    print(f"Environment: {data['environment']}")
    print(f"Boot Source: {data['boot_source']}")
    print(f"Runtime Mode: {data['runtime_mode']}")
    print(f"Hostname: {data['hostname']}")
    
    # 2. Check Service Stack status
    services = data["services"]
    print(f"Active Services: {len(services)}")
    for svc in services:
        print(f" - {svc['name']}: {svc['status']}")

    # 3. Check node provisioning
    res = requests.get(f"{BASE_URL}/cluster/state", params={"user_id": CREATOR_ID})
    state = res.json()
    print(f"Cluster Node Count: {len(state['nodes'])}")
    local_node = next((n for n in state['nodes'] if n['node_id'].startswith("node-")), None)
    if local_node:
        print(f"Local Provisioned Node: {local_node['node_id']} ({local_node['node_status']})")

if __name__ == "__main__":
    print("Bootable runtime test script ready.")
    # test_bootable_runtime()
