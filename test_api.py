import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Testing general chat
        payload = {"message": "hola"}
        response = await client.post("http://localhost:8000/api/v1/ai-host/process", json=payload)
        print("Response for 'hola':", response.json())
        
        # Testing detailed question
        payload2 = {"message": "explica omniweb detallado"}
        response2 = await client.post("http://localhost:8000/api/v1/ai-host/process", json=payload2)
        print("Response for 'explica':", response2.json())

        # Testing fallback bug
        payload3 = {"message": "habla de cualquier cosa"}
        response3 = await client.post("http://localhost:8000/api/v1/ai-host/process", json=payload3)
        print("Response for 'habla':", response3.json())

if __name__ == "__main__":
    asyncio.run(test_api())
