import asyncio
import json
from backend.core.ai_host.observability.governance_chat_engine import chat_governance_engine
from backend.core.permissions import set_chip_context

async def validate_chat_logic():
    print("--- VALIDATING CHAT GOVERNANCE LOGIC (INTERNAL) ---")
    
    # We must be in a trusted context (e.g. core or ai-host)
    with set_chip_context("core"):
        # Message: Fragile domain (auth) + Intent (borrar)
        message = "Quiero borrar el viejo sistema de auth por un router nuevo."
        context = {"user_id": "creator-001", "conversation_id": "test-conv-99"}
        
        # Trigger interaction analysis
        signals = await chat_governance_engine.analyze_interaction(message, context)
        
        print(f"RESULT: Generated {len(signals)} signals.")
        for s in signals:
            print(f"[{s.severity_band}] {s.signal_type}: {s.rationale}")
            if s.suggested_adjustment:
                print(f"      -> SUGGESTION: {s.suggested_adjustment}")

        # Verify cooldown
        print("\n--- Testing Cooldown (Same message context) ---")
        signals_cd = await chat_governance_engine.analyze_interaction(message, context)
        print(f"Cooldown check: Found {len(signals_cd)} signals. {'PASS' if len(signals_cd) == 0 else 'FAIL'}")

if __name__ == "__main__":
    asyncio.run(validate_chat_logic())
