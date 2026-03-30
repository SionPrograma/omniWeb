import asyncio
import os
import json
import logging
from unittest.mock import patch, AsyncMock

# Add test path manually
os.environ["COGNITIVE_API_KEY"] = "fake-key"
os.environ["OMNIWEB_MODE"] = "creator"

from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.routing.command_router import CommandRouter

logger = logging.getLogger('backend.core.ai_host.brain_router')
logger.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
logger.addHandler(ch)

async def test_integration():
    global command_router, brain_router
    # Mocking external state
    class MockCommandRouter:
        registry = type('MockRegistry', (), {'get_processor': lambda s, n: None})()
    
    command_router = MockCommandRouter()
    brain_router = BrainRouter(command_router)
    
    # Context mock
    ctx = {"user_id": "default_user"}

    print("\n--- TEST 1: FAST PATH (Abre modulo) ---")
    res = await brain_router.process("abre chip finanzas", context=ctx)
    print("Intent:", res.intent if res else "None")

    print("\n--- TEST 2: FALLBACK (L2 Pincha) ---")
    res = await brain_router.process("analiza la latencia del microservicio", context=ctx)
    print("Intent:", res.intent if res else "None")
    print("Message:", res.message[:100] if res else "None")

    print("\n--- TEST 3: L2 SUCCESS (Groq responde bien) ---")
    fake_json = json.dumps({
        "choices": [{
            "message": {
                "content": '{"semantic_target": "analizar_latencia", "technical_hypothesis": "Podria ser un GC pause", "decision_mode": "reflective_analysis", "actionable_chips": ["chip-finanzas"], "requires_clarification": false, "confidence_score": 0.95, "constraints": []}'
            }
        }]
    })

    with patch('httpx.AsyncClient.post') as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = json.loads(fake_json)
        mock_response.raise_for_status = lambda: None
        mock_post.return_value = mock_response

        res = await brain_router.process("analiza la latencia del microservicio", context=ctx)
        print("Intent:", res.intent if res else "None")
        print("Message:")
        print(res.message if res else "None")

asyncio.run(test_integration())
