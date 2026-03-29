
import asyncio
import json
import logging
import sys
import os
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger()

# Add project root to sys.path
sys.path.append(os.getcwd())

async def run_block2_evals():
    from backend.core.ai_host.orchestration.cognitive_orchestrator import CognitiveOrchestrator
    from backend.core.permissions import set_chip_context
    from backend.core.ai_host.intent_understanding.intent_engine import intent_engine
    from backend.core.ai_host.observability.tracing_api import tracing_api
    
    orchestrator = CognitiveOrchestrator()
    
    eval_cases = [
        {"id": 1, "name": "Saludo Casual", "input": "hola omni", "expected_mode": "natural_chat", "min_mem": 0},
        {"id": 2, "name": "Comando de Sistema", "input": "inspeccioná el chip finanzas", "expected_mode": "action_execution", "min_mem": 1},
        {"id": 3, "name": "Consulta Memoria/Proyecto", "input": "qué recordás del roadmap?", "expected_intent_group": "MEMORY_INTENT", "min_mem": 1},
        {"id": 4, "name": "Ambigüedad", "input": "ayudame con eso", "expected_mode": "natural_chat"},
        {"id": 5, "name": "Caso Técnico SOLO", "input": "SOLO archivo_leido de CogOrch", "expected_mode": "constrained_output", "min_mem": 1},
        {"id": 6, "name": "Consulta de Estado Global", "input": "cuál es el estado del sistema?", "expected_mode": "action_execution", "min_mem": 1}
    ]
    
    print("="*80)
    print(" OMNIWEB BLOCK 2 - BASE EVALUATION SUITE ")
    print("="*80 + "\n")
    
    results = []
    
    for case in eval_cases:
        print(f"--- RUNNING EVAL {case['id']}: {case['name']} ---")
        print(f"INPUT: '{case['input']}'")
        
        try:
            with set_chip_context("core", user_id="eval_user"):
                understanding = await intent_engine.understand(case["input"], "eval_user")
                response = await orchestrator.orchestrate(
                    message=case["input"],
                    understanding=understanding,
                    context={"user_id": "eval_user"}
                )
                
                # Retrieve the last trace finalized
                trace = tracing_api.get_recent_traces(1)[0]
                
                # Check criteria
                passed = True
                fail_reason = ""
                
                if "expected_mode" in case and trace.response_mode != case["expected_mode"]:
                    passed = False
                    fail_reason += f"Mode mismatch: got {trace.response_mode}, expected {case['expected_mode']}. "
                
                if "min_mem" in case and trace.memory_refs_count < case["min_mem"]:
                    passed = False
                    fail_reason += f"Memory mismatch: got {trace.memory_refs_count} refs, expected >= {case['min_mem']}. "
                
                print(f"RESULT: {'[PASS]' if passed else '[FAIL]'}")
                if not passed: print(f"REASON: {fail_reason}")
                
                print(f"TRACE_ID: {trace.trace_id}")
                print(f"TOOLS: {trace.candidate_tools} -> SELECTED: {trace.selected_tool}")
                print(f"DIAGNOSTICS: {trace.diagnostics}")
                print(f"LATENCY: {trace.latency_total:.4f}s")
                print("-" * 40 + "\n")
                
                results.append({
                    "case": case["name"],
                    "passed": passed,
                    "diagnostics": trace.diagnostics,
                    "latency": trace.latency_total
                })
        except Exception as e:
            print(f"[!] SYSTEM ERROR during eval: {e}")
            results.append({"case": case["name"], "passed": False, "error": str(e)})

    # Summary
    print("="*80)
    print(" EVALUATION SUMMARY ")
    print("="*80)
    passed_count = sum(1 for r in results if r["passed"])
    print(f"TOTAL CASES: {len(results)}")
    print(f"PASSED: {passed_count}")
    print(f"FAILED: {len(results) - passed_count}")
    print("="*80)

if __name__ == "__main__":
    asyncio.run(run_block2_evals())
