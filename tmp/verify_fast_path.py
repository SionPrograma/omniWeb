import asyncio
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.core.ai_host.routing.command_router import CommandRouter

async def test_fast_path():
    router = CommandRouter()
    
    test_cases = [
        ("hola", True),
        ("que tal?", True),
        ("quien eres?", True),
        ("perfecto", True),
        ("analiza el archivo core.py", False), # Tech signals
        ("omni hola", False), # Creator prefixed
        ("chiste", True),
        ("todo bien", True),
        ("me siento mal", True), # Word count <= 2 and no tech signals
        ("instalar dependencia x en el sistema", False), # tech signals 'sistema'
    ]
    
    print("\n--- Verifying Fast-Path Logic ---")
    for msg, expected_fast in test_cases:
        # Check direct logic
        msg_clean = msg.lower().strip()
        is_creator_prefixed = any(msg_clean.startswith(p) for p in ["omni", "creator", "system"])
        
        fast_category = router._is_local_fast_path(msg_clean, "chat")
        is_fast = not is_creator_prefixed and fast_category is not None
        
        status = "PASS" if is_fast == expected_fast else "FAIL"
        print(f"Input: '{msg}' | Fast-Path: {is_fast} | Expected: {expected_fast} | [{status}]")
        if fast_category:
             print(f"   -> Category: {fast_category}")

if __name__ == "__main__":
    asyncio.run(test_fast_path())
