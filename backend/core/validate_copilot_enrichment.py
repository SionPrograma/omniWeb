import asyncio
import httpx
import json

async def validate_copilot_enrichment():
    print("--- VALIDATING MISSION CO-PILOT ENRICHMENT ---")
    
    # We use a known surface that has friction in our previous sessions
    payload = {
        "objective": "Reemplazar completamente el sistema de autenticación por uno nuevo borrando las tablas viejas.",
        "surface": ["core_auth", "auth_gate"]
    }
    
    headers = {
        "Authorization": "Bearer omniweb-dev-secret-token",
        "Content-Type": "application/json"
    }
    
    async with httpx.AsyncClient() as client:
        # 1. Trigger enrichment
        print(f"Requesting enrichment for: {payload['objective']}")
        res = await client.post("http://localhost:8000/api/v1/governance/copilot/enrich", json=payload, headers=headers)
        
        if res.status_code == 200:
            data = res.json()
            print(f"SUCCESS: Received {data['count']} enrichment signals.")
            for s in data['signals']:
                print(f"[{s['severity']}] {s['signal_type']}: {s['rationale'][:100]}...")
                if s['suggested_adjustment']:
                    print(f"      -> SUGGESTION: {s['suggested_adjustment']}")
        else:
            print(f"FAILED: {res.status_code} - {res.text}")

if __name__ == "__main__":
    asyncio.run(validate_copilot_enrichment())
