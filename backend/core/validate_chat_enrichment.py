import asyncio
import httpx
import json

async def validate_chat_enrichment():
    print("--- VALIDATING GOVERNANCE CHAT ENRICHMENT ---")
    
    # Payload for a message that mentions a fragile domain and an intent
    payload = {
        "message": "Quiero implementar cambios en el auth para borrar el viejo router.",
        "multimodal_evidence": [],
        "source_surface": "chat"
    }
    
    headers = {
        "Authorization": "Bearer omniweb-dev-secret-token",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        print(f"Sending message: {payload['message']}")
        res = await client.post("http://localhost:8000/api/v1/ai-host/process", json=payload, headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            print("SUCCESS: AI processed the message.")
            if "gov_enrichment" in data:
                enrich = data["gov_enrichment"]
                print(f"Detected {enrich['count']} governance signals in chat.")
                for s in enrich["signals"]:
                    print(f"[{s['severity_band']}] {s['signal_type']}: {s['rationale'][:100]}...")
                    if s["suggested_adjustment"]:
                        print(f"      -> SUGGESTED: {s['suggested_adjustment']}")
            else:
                print("FAIL: No governance enrichment in response.")
        else:
            print(f"FAILED: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(validate_chat_enrichment())
