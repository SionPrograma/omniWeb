import asyncio
import logging
import sys
import os

# Setup path to include backend
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))

from backend.core.ai_host.routing.command_router import ai_command_router
from backend.core.ai_host.processors.base import AICommandResponse

# Configure logging to capture our "UNIFY_LAYER_EXECUTED" marker
log_stream = []
class ListHandler(logging.Handler):
    def emit(self, record):
        log_stream.append(record.getMessage())

root_logger = logging.getLogger()
root_logger.setLevel(logging.INFO)
root_logger.addHandler(ListHandler())

async def run_audit():
    test_cases = [
        {"name": "Robotic System Status", "msg": "test_jargon", "mock_msg": "The system is currently in HEALTHY state with 0 active chips."},
        {"name": "Technical Anomaly", "msg": "test_anomaly", "mock_msg": "Primary anomaly detected in flow.ai_to_chips.latency. Detected performance degradation."},
        {"name": "Mixed Language", "msg": "test_mixed", "mock_msg": "System status is nominal. Success in executing background tasks."},
        {"name": "Complex Reasoning", "msg": "analiza el rendimiento del sistema"}
    ]

    print("\n=== STARTING PIPELINE AUDIT ===\n")

    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    orchestrator = CognitiveOrchestrator(ai_command_router)

    for case in test_cases:
        log_stream.clear()
        print(f"Testing: {case['name']} ('{case['msg']}')")
        
        try:
            if "mock_msg" in case:
                mock_res = AICommandResponse(intent="test", status="success", message=case["mock_msg"])
                response = await orchestrator.orchestrate(
                    message=case["msg"],
                    understanding={"mode": "direct_response", "intent_group": "TEST"},
                    raw_response=mock_res
                )
            else:
                response = await ai_command_router.route(case["msg"], context={"user_id": "audit_user"})
            
            # Check for the unified layer marker
            unified_executed = any("UNIFY_LAYER_EXECUTED" in log for log in log_stream)
            
            # Forbidden markers (system-style)
            system_style = ["The system is", "System status", "Primary anomaly", "Detected performance"]
            has_system_style = any(s.lower() in response.message.lower() for s in system_style)
            
            print(f"  - Unify Layer Hit: {unified_executed}")
            print(f"  - Humanized: {not has_system_style}")
            print(f"  - Tone Check: {'CONVERSATIONAL' if len(response.message) > 5 else 'ROBOTIC'}")
            print(f"  - Response: {response.message}")
            
            if has_system_style:
                print(f"  [!] FAIL: Robotic markers detected in output")
                
        except Exception as e:
            print(f"  [!] CRITICAL ERROR during test: {e}")

    print("\n=== AUDIT COMPLETE ===\n")

if __name__ == "__main__":
    asyncio.run(run_audit())
