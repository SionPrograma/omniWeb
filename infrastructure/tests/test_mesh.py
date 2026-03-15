import requests
import json
import time

BASE_URL = "http://localhost:8000/api/v1/system/cluster/mesh"
CREATOR_ID = "1"

def test_mesh():
    print("--- PHASE 26 TEST: MESH NETWORKING LAYER ---")
    
    # 1. Trigger Discovery (Implicit in state fetch)
    res = requests.get(f"{BASE_URL}/state", params={"user_id": CREATOR_ID})
    state = res.json()
    print(f"Mesh Local Node: {state['node_id']}")
    print(f"Mesh Health: {state['network_health']*100}%")
    print(f"Active Peers: {state['connected_peers']}")

    # 2. Simulate P2P Message
    message = {
        "type": "gossip_update",
        "data": {"worker_load": 0.45, "active_chips": 12}
    }
    res = requests.post(f"{BASE_URL}/message", json=message, params={"user_id": CREATOR_ID, "target_node_id": "worker-node-02"})
    print(f"Dispatch P2P Message: {res.status_code}")
    print(f"Peer Response: {res.json()}")

    # 3. Verify Peer Entry
    res = requests.get(f"{BASE_URL}/state", params={"user_id": CREATOR_ID})
    state = res.json()
    if state['peers']:
        peer = state['peers'][0]
        print(f"Peer 01: {peer['node_id']} | Latency: {peer['latency']:.1f}ms | Status: {peer['status']}")

if __name__ == "__main__":
    print("Mesh test script ready.")
    # test_mesh()
