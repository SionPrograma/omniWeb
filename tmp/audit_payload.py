
import asyncio
import logging
import sys
import os

# Add project root to sys.path
project_root = r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb"
sys.path.append(project_root)

# Configure logging
logging.basicConfig(level=logging.ERROR)

from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator

async def audit_payload():
    print("\n=== AUDITING COGNITIVE ORCHESTRATOR PAYLOAD ===")
    orchestrator = CognitiveOrchestrator()
    
    # Simulate a request that would trigger a mission (e.g. Creator command keywords)
    message = "Audita el módulo core/module.py y propón una mejora."
    understanding = {
        "intent_group": "SYSTEM_AUDIT_INTENT",
        "specific_intent": "system_audit",
        "mode": "constrained_output",
        "confidence": 0.95,
        "context": None
    }
    context = {"user_id": "auditor_real"}
    
    try:
        # Mocking the brain response to simulate mission execution being called
        from backend.core.ai_host.processors.base import AICommandResponse
        mock_res = AICommandResponse(
            intent="swarm_orchestration",
            status="success",
            message="Simulated result",
            payload={"mission_title": "Audit core/module.py", "execution_details": {"shadows": [], "constructors": []}}
        )
        
        # We call synthesize_response directly to see how it handles the payload
        final_res = await orchestrator.synthesize_response(
            message=message,
            brain_response=mock_res,
            system_state=None,
            understanding=understanding,
            recent_context=[],
            session_id="auditor_real",
            context=context
        )
        
        print(f"Goal: {message}")
        print(f"Payload keys: {list(final_res.payload.keys())}")
        if "task_tree" in final_res.payload:
            print("  Check: task_tree present.")
        if "policy_result" in final_res.payload:
            print("  Check: policy_result present.")
        if "execution_details" in final_res.payload:
            print("  Check: mission data preserved.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(audit_payload())
