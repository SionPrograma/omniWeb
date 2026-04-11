from .base_adapter import BaseIntelligenceAdapter, CapabilityClass, TrustBand, OutcomeStatus
from .ledger import forge_ledger
import time
import asyncio

class MockTranslationAdapter(BaseIntelligenceAdapter):
    """
    Validation Stub for Intelligence Forge.
    Demonstrates how a real provider would report telemetry.
    """
    def __init__(self):
        super().__init__(
            provider_id="mock_lingua_v1",
            capability=CapabilityClass.TRANSLATION,
            trust=TrustBand.EXPERIMENTAL
        )

    async def invoke(self, payload: str, context: str = "generic") -> dict:
        start_time = time.time()
        
        # Simulate local/mock processing
        await asyncio.sleep(0.1) 
        translated = f"[MOCK_AUTOPILOT] {payload}"
        
        latency = int((time.time() - start_time) * 1000)
        
        # Report telemetry to Forge Ledger
        telemetry = self.create_telemetry_receipt(
            outcome=OutcomeStatus.SUCCESS,
            latency_ms=latency,
            quality=1.0,
            cost_units=0.001,
            task_context=context
        )
        await forge_ledger.log_telemetry(telemetry)
        
        return {
            "result": translated,
            "telemetry": telemetry
        }
