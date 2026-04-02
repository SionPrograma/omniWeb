import asyncio
import sys
import os
import json

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.main import app
from httpx import AsyncClient

async def test_chat_backend():
    print("\n--- Testing Backend Chat Interaction ---")
    async with AsyncClient(app=app, base_url="http://test") as ac:
        response = await ac.post("/api/v1/ai-host/process", json={
            "message": "hola",
            "multimodal_evidence": [],
            "source_surface": "chat"
        }, headers={"Authorization": "Bearer omniweb-dev-secret-token"})
        
        print(f"Status Code: {response.status_code}")
        if response.status_code == 200:
            print("SUCCESS: Backend responded.")
            data = response.json()
            print(f"Response Message: {data.get('message', 'NONE')[:100]}...")
        else:
            print(f"FAILED: {response.text}")

if __name__ == "__main__":
    asyncio.run(test_chat_backend())
