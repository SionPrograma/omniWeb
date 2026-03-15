import asyncio
import httpx
import json

BASE_URL = "http://localhost:8000/api/v1/ai-host/copilot"
HEADERS = {"Authorization": "Bearer omniweb-dev-secret-token"}

async def test_copilot_flow():
    async with httpx.AsyncClient() as client:
        print("\n--- [STEP 1] Generating Plan ---")
        prompt = "Create a new logistics optimization module"
        res = await client.post(f"{BASE_URL}/plan", json={"prompt": prompt}, headers=HEADERS)
        
        if res.status_code != 200:
            print(f"Error generating plan: {res.text}")
            return
            
        plan = res.json()
        plan_id = plan["id"]
        print(f"Plan generated: {plan_id}")
        print(f"Steps: {[s['description'] for s in plan['steps']]}")

        print("\n--- [STEP 2] Executing Steps ---")
        for step in plan["steps"]:
            step_id = step["id"]
            print(f"Executing step: {step['description']}")
            exec_res = await client.post(
                f"{BASE_URL}/execute-step", 
                json={"plan_id": plan_id, "step_id": step_id},
                headers=HEADERS,
                timeout=30.0
            )
            
            if exec_res.status_code == 200:
                print(f"  Result: Success")
            else:
                print(f"  Result: Failed - {exec_res.text}")
                break

        print("\n--- [STEP 3] Final Plan Status ---")
        final_res = await client.get(f"{BASE_URL}/plan/{plan_id}", headers=HEADERS)
        final_plan = final_res.json()
        print(f"Final Status: {final_plan['status']}")

if __name__ == "__main__":
    # Note: Make sure the server is running on localhost:8000
    try:
        asyncio.run(test_copilot_flow())
    except Exception as e:
        print(f"Test failed: {e}")
