import asyncio
import json
from backend.core.ai_host.observability.governance_copilot_engine import governance_copilot

async def validate_copilot_logic():
    print("--- VALIDATING MISSION CO-PILOT LOGIC (INTERNAL) ---")
    
    # Payload for simulation
    objective = "Reemplazar el router por uno mas ligero borrando lo viejo."
    surface = ["core_router", "api_gateway"]
    
    # Trigger analysis
    signals = await governance_copilot.analyze_draft(objective, surface)
    
    print(f"RESULT: Found {len(signals)} signals.")
    for s in signals:
        print(f"[{s.severity}] {s.signal_type}: {s.rationale}")
        if s.suggested_adjustment:
            print(f"      -> SUGGESTION: {s.suggested_adjustment}")
            
    # Check if we got expected signals for 'borrar' and drift-prone surface
    borrar_detected = any(s.signal_type == "ARCHITECTURAL_ANTIPATTERN" for s in signals)
    print(f"Antipattern check: {'PASS' if borrar_detected else 'FAIL'}")

if __name__ == "__main__":
    asyncio.run(validate_copilot_logic())
