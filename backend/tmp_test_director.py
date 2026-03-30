import asyncio
from backend.core.ai_host.brain_router import BrainRouter
from backend.core.ai_host.processors.base import AICommandResponse
import json

# Minimal Mock for CommandRouter
class MockRegistry:
    def get_processor(self, name):
        class MockProc:
            async def can_handle(self, msg): return True
            async def process(self, msg, context=None):
                return AICommandResponse(intent="chat", status="success", message=f"Respuesta de {name}")
        return MockProc()

class MockCommandRouter:
    def __init__(self):
        self.registry = MockRegistry()

class MockEvidenceBundle:
    def __init__(self):
        self.snapshot_id = "test-snapshot-123"
        self.has_sufficient_evidence = True
        self.items = []


class MockDelibContext:
    def __init__(self):
        self.recent_topic = "latency"
        self.evidence_bundle = MockEvidenceBundle()

async def test_director_flow():
    print("=== TEST: BRAIN ROUTER COMO DIRECTOR REAL ===")
    router = BrainRouter(MockCommandRouter())
    
    # Mocking deliberation_engine.assemble_context
    from backend.core.ai_host.deliberation.deliberation_engine import deliberation_engine
    import unittest.mock as mock
    deliberation_engine.assemble_context = mock.AsyncMock(return_value=MockDelibContext())

    print("\n[TEST A: GREETING (FAST-PATH)]")
    res_a = await router.process("hola omni", understanding={"intent_group": "GREETING", "mode": "conversational"})
    print(f"Intención: {res_a.intent} | Mensaje: {res_a.message}")

    # Escenario B: TECHNICAL (Latencia)
    print("\n[TEST B: TECHNICAL (LOCAL BRAIN)]")
    # Este disparará el pipeline estructurado que probamos antes
    res_b = await router.process("por qué tarda tanto?", understanding={"intent_group": "DIAGNOSTIC", "specific_intent": "system_audit", "mode": "diagnostic"})
    print(f"Intención: {res_b.intent}")
    print(f"Mensaje (Primeras líneas):\n{res_b.message.splitlines()[0]}")

    # Escenario C: CONVERSATIONAL (Natural Chat)
    print("\n[TEST C: CONVERSATIONAL (CHAT)]")
    res_c = await router.process("qué opinas del clima?", understanding={"intent_group": "NATURAL_CHAT", "mode": "conversational"})
    print(f"Intención: {res_c.intent} | Mensaje: {res_c.message}")

if __name__ == "__main__":
    asyncio.run(test_director_flow())
