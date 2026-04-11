import asyncio
import logging
import sys
import os

# Set up logging to stdout
logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger(__name__)

# Add workspace to path
sys.path.append(os.getcwd())

async def test_creator_gateway_integration():
    from backend.core.ai_host.brain_router import BrainRouter
    
    # Mocking command_router
    class MockRouter:
        def __init__(self):
            self.registry = type('obj', (object,), {'get_processor': lambda x: None})
            self.intents = {}

    router = BrainRouter(MockRouter())
    
    # Test message
    msg = "fix the issue"
    context = {"source_surface": "chat", "user_id": "creator_1", "intent": "healing", "target_files": ["README.md"]}
    
    print("\n--- PHASE B VERIFICATION ---")
    print(f"Feeding message: '{msg}' with source_surface='chat'")
    
    # We don't need to await the full process if we just want to see the logs 
    # and check if context was updated.
    # But since process is async and has many imports/side effects, we'll try a light run.
    
    try:
        # We expect it to fail later due to missing dependencies in the mock, 
        # but the normalization happens at the very beginning.
        await router.process(msg, context=context)
    except Exception as e:
        print(f"Stopped at: {e}")

    print("Verification complete. Check logs for [CREATOR_GATEWAY] and [CREATOR_UNISON].")

if __name__ == "__main__":
    asyncio.run(test_creator_gateway_integration())
