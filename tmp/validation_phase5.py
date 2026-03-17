import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"
TOKEN = "omniweb-dev-secret-token"
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Content-Type": "application/json"
}

def test_query(message):
    print(f"\n--- TESTING: {message} ---")
    data = {"message": message}
    try:
        response = requests.post(f"{BASE_URL}/ai-host/process", headers=HEADERS, json=data)
        if response.status_code == 200:
            res_data = response.json()
            print(f"INTENT: {res_data.get('intent', 'unknown')}")
            print(f"MESSAGE:\n{res_data.get('message', 'No message')}")
        else:
            print(f"ERROR: {response.status_code} - {response.text}")
    except Exception as e:
        print(f"EXCEPTION: {e}")

# Wait for server to be fully ready
print("Waiting 3 seconds for server startup...")
time.sleep(3)

queries = [
    "analiza el sistema y dime qué observas",
    "¿qué está pasando realmente con tu sistema ahora?",
    "te estuve probando hace un rato, ¿qué puedes inferir de eso?",
    "usa el contexto de esta conversación para responder mejor",
    "si tuvieras que mejorar tu arquitectura, ¿qué harías?"
]

for q in queries:
    test_query(q)
    time.sleep(1)
