
import asyncio
import json
import logging
import sys
import os

# Configure logging to capture output
log_stream = []
class ListHandler(logging.Handler):
    def emit(self, record):
        log_stream.append(self.format(record))

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
handler = ListHandler()
handler.setFormatter(logging.Formatter('%(message)s'))
logger.addHandler(handler)

# Add the project root to sys.path
sys.path.append(os.getcwd())

async def run_final_verification():
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.permissions import set_chip_context
    from backend.core.ai_host.intent_understanding.intent_engine import intent_engine
    
    orchestrator = CognitiveOrchestrator()
    
    test_cases = [
        {"id": 1, "name": "Caso Casual", "input": "hola omni, cómo estás?"},
        {"id": 2, "name": "Caso Ambiguo", "input": "ayudame con eso"}
    ]
    
    print("="*60)
    print(" VERIFICACIÓN FINAL BLOQUE 1 - CASOS CRÍTICOS ")
    print("="*60 + "\n")
    
    for case in test_cases:
        print(f"--- TEST {case['id']}: {case['name']} ---")
        print(f"INPUT: '{case['input']}'")
        
        log_stream.clear()
        
        try:
            with set_chip_context("core", user_id="test_user"):
                # 1. Intent Understanding
                understanding = await intent_engine.understand(case["input"], "test_user")
                
                # 2. Orchestration
                response = await orchestrator.orchestrate(
                    message=case["input"],
                    understanding=understanding,
                    context={"user_id": "test_user"}
                )
                
                # Extract results
                intent_group = understanding.get("intent_group")
                mode = understanding.get("mode")
                
                has_internal_out = any("Internal Trace" in log for log in log_stream)
                internal_trace = "N/A"
                if has_internal_out:
                    trace_log = [log for log in log_stream if "Internal Trace" in log][0]
                    internal_trace = trace_log.split("Internal Trace: ", 1)[1]

                print(f"INTENCIÓN DETECTADA: {intent_group}")
                print(f"MODO / RUTA TOMADA: {mode}")
                print(f"INTERNAL_TRACE: {internal_trace}")
                print(f"RESPUESTA FINAL: {response.message}")
                print("-" * 30 + "\n")
                
        except Exception as e:
            print(f"[!] FAIL: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(run_final_verification())
