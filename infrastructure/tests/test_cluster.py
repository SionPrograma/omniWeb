import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/system/cluster"
CREATOR_ID = "1"

def test_cluster():
    print("--- PHASE 24 TEST: CLUSTER INFRASTRUCTURE ---")
    
    # 1. Register a worker node
    node_data = {
        "node_id": "worker-node-02",
        "node_role": "worker",
        "node_region": "us-west",
        "node_url": "http://worker-02:8000",
        "node_secret": "secret-phase-24",
        "connected_services": ["ai-inference", "chip-executor"]
    }
    res = requests.post(f"{BASE_URL}/register", json=node_data, params={"user_id": CREATOR_ID})
    print(f"Register Node: {res.status_code}")

    # 2. Send Heartbeats
    for i in range(3):
        hb = {
            "node_id": "worker-node-02",
            "cpu_usage": 0.35 + (i * 0.05),
            "memory_usage": 0.42,
            "active_chips": 5 + i,
            "latency": 15.0 + i
        }
        res = requests.post(f"{BASE_URL}/heartbeat", json=hb)
        print(f"Heartbeat {i+1}: {res.status_code}")
        time.sleep(1)

    # 3. Check Cluster State
    res = requests.get(f"{BASE_URL}/state", params={"user_id": CREATOR_ID})
    state = res.json()
    print(f"Cluster State: {state['active_nodes']} active nodes found.")
    for node in state['nodes']:
        print(f" - Node {node['node_id']} ({node['node_role']}): {node['node_status']} | CPU: {node['cpu_usage']:.2f}")

    # 4. Test Node Operation (Drain)
    op = {"operation": "drain", "target_node_id": "worker-node-02"}
    res = requests.post(f"{BASE_URL}/operation", json=op, params={"user_id": CREATOR_ID})
    print(f"Drain Operation: {res.status_code}")

    # 5. Verify Status Change
    res = requests.get(f"{BASE_URL}/state", params={"user_id": CREATOR_ID})
    state = res.json()
    node2 = next(n for n in state['nodes'] if n['node_id'] == "worker-node-02")
    print(f"Node 02 Status after Drain: {node2['node_status']}")

if __name__ == "__main__":
    print("Test script ready. Run with server active.")
    # test_cluster()
