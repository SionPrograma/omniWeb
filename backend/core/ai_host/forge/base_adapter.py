from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Any
from datetime import datetime
import uuid

class CapabilityClass(Enum):
    TRANSLATION = "translation"
    TRANSCRIPTION = "transcription"
    SYNTHESIS = "synthesis"
    COGNITION = "cognition"
    RETRIEVAL = "retrieval"
    EXECUTION = "execution"

class OutcomeStatus(Enum):
    SUCCESS = "success"
    PARTIAL = "partial"
    FAIL = "fail"
    TIMEOUT = "timeout"

class TrustBand(Enum):
    SOVEREIGN_NATIVE = "sovereign_native" # Local/OS Models
    PUBLIC_CLOUD = "public_cloud"       # SaaS (e.g. Google)
    EXPERIMENTAL = "experimental"       # Unvalidated/Untrusted

class BaseIntelligenceAdapter(ABC):
    """
    Forge Base Adapter (Block 77).
    A standardized contract for every external tool/AI provider Omni observes.
    """
    def __init__(self, provider_id: str, capability: CapabilityClass, trust: TrustBand):
        self.provider_id = provider_id
        self.capability = capability
        self.trust = trust

    @abstractmethod
    async def invoke(self, payload: Any, context: Optional[dict] = None) -> dict:
        """
        Executes the external capability.
        Returns a standardised response including the primary result.
        """
        pass

    def create_telemetry_receipt(
        self, 
        outcome: OutcomeStatus, 
        latency_ms: int, 
        quality: float = 0.0, 
        cost_units: float = 0.0,
        task_context: str = "generic"
    ) -> dict:
        """
        Standardizes the telemetry payload for the Forge Ledger.
        """
        return {
            "provider_id": self.provider_id,
            "capability_class": self.capability.value,
            "task_context": task_context,
            "outcome_status": outcome.value,
            "quality_score": max(0.0, min(1.0, quality)),
            "latency_ms": latency_ms,
            "cost_units": cost_units,
            "privacy_band": self.trust.value,
            "timestamp": datetime.utcnow().isoformat()
        }
