import requests

BASE_URL = "http://127.0.0.1:8000"
TOKEN = "omniweb-dev-secret-token"

def test_knowledge_dialogue():
    print("Testing Knowledge Dialogue: 'explain thermodynamics'...")
    headers = {"Authorization": f"Bearer {TOKEN}"}
    r = requests.post(
        f"{BASE_URL}/api/v1/ai-host/process",
        json={"message": "explain thermodynamics"},
        headers=headers
    )
    
    if r.status_code == 200:
        data = r.json()
        print(f"Data: {data}")
        if 'text' in data:
            print(f"Response: {data['text']}")
            if "thermodynamics" in data['text'].lower() or "conocimiento" in data['text'].lower():
                print("[PASS] Knowledge intent verified.")
            else:
                print(f"[PARTIAL] AI Host responded: {data['text']}")
        else:
             print(f"[FAIL] Response missing text key. Keys: {data.keys()}")
    else:
        print(f"[FAIL] AI Host returned {r.status_code}")

if __name__ == "__main__":
    test_knowledge_dialogue()
