
import requests
import json

def validate_atlas_enrichment():
    node_id = "WNODE-TEST-001"
    url = f"http://localhost:8000/api/v1/governance/wisdom/atlas/node/{node_id}"
    
    try:
        # Mocking auth token if needed, but assuming dev server lets it through
        response = requests.get(url, headers={"Authorization": "Bearer TEST_TOKEN"})
        data = response.json()
        
        if data["status"] == "success":
            payload = data["payload"]
            print(f"Node: {payload['title']}")
            print(f"Confidence: {payload['confidence']}")
            print(f"Evidence Summary: {json.dumps(payload['evidence_summary'], indent=2)}")
            print(f"Sync History Count: {len(payload['sync_history'])}")
            
            summary = payload["evidence_summary"]
            if summary["total_syncs"] == 5 and summary["WISDOM_CONFIRMED"] >= 1:
                print("--- VALIDATION SUCCESSFUL ---")
            else:
                print("--- VALIDATION FAILED: Counts mismatch ---")
        else:
            print(f"API Error: {data['message']}")
    except Exception as e:
        print(f"API Connection Error: {e}")

if __name__ == "__main__":
    validate_atlas_enrichment()
