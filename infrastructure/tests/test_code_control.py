import asyncio
import json
from backend.core.ai_host.command_router import ai_command_router

async def test_code_control():
    print("\n--- Testing Code Control Layer ---")
    
    # 1. Test Inspection
    print("\n[TEST 1] Inspecting shell code...")
    resp = await ai_command_router.route("inspect shell code")
    print(f"Status: {resp.status}")
    print(f"Message: {resp.message}")
    if resp.payload.get("visual"):
        print(f"Visual Payload Type: {resp.payload['visual']['type']}")
    
    # 2. Test Patch Proposal
    print("\n[TEST 2] Proposing fix for lingua button...")
    resp = await ai_command_router.route("fix button in lingua")
    print(f"Intent: {resp.intent}")
    print(f"Message: {resp.message}")
    
    # 3. Test Patch Confirmation
    if resp.intent == "confirmation_required":
        print("\n[TEST 3] Confirming patch...")
        resp_confirm = await ai_command_router.route("confirm fix button in lingua")
        print(f"Status: {resp_confirm.status}")
        print(f"Message: {resp_confirm.message}")

if __name__ == "__main__":
    asyncio.run(test_code_control())
