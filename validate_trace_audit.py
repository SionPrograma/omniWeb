
import requests
import json

def validate_trace_deep_linking():
    trace_id = "CAT-AUDIT-TEST-99"
    url = f"http://localhost:8000/api/v1/governance/catalyst/trace/{trace_id}"
    
    try:
        response = requests.get(url, headers={"Authorization": "Bearer TEST_TOKEN"})
        data = response.json()
        
        if data["status"] == "success":
            payload = data["payload"]
            print(f"Trace {trace_id} Audit Events: {len(payload)}")
            for i, evt in enumerate(payload):
                print(f"[{i}] Event: {evt['decision_type']} - {evt['created_at']}")
            
            if len(payload) == 2:
                print("--- VALIDATION SUCCESSFUL: 2 Audit Events found ---")
            else:
                print(f"--- VALIDATION FAILED: Expected 2 events, got {len(payload)} ---")
        else:
            print(f"API Error: {data['message']}")
    except Exception as e:
        print(f"API Connection Error: {e}")

if __name__ == "__main__":
    validate_trace_deep_linking()
