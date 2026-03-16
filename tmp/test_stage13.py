import sys
import os
import asyncio
import logging

# Set up paths
sys.path.append(os.getcwd())

# Mock logging
logging.basicConfig(level=logging.INFO)

async def test_stage13_stabilization():
    from backend.core.ai_host.cognition.cognitive_core import cognitive_core
    from backend.core.ai_host.reasoning.evidence_engine import evidence_engine
    from backend.core.ai_host.execution.execution_controller import execution_controller
    from backend.core.ai_host.learning.adaptive_learning import adaptive_learning
    from backend.core.ai_host.brain_router import BrainRouter
    from backend.core.chips.chip_orchestrator import chip_orchestrator
    
    class MockRegistry:
        def get_processor(self, name): return None

    # Mock command router
    async def mock_intent(msg):
        return AICommandResponse(intent="mock", status="success", message="Mocked Response")

    class MockCommandRouter:
        def __init__(self):
            self.intents = {
                "open_chip": mock_intent,
                "inspect_chip": mock_intent
            }
            self.registry = MockRegistry()
            self._handle_show_system_status = mock_intent

    brain_router = BrainRouter(MockCommandRouter())

    print("\n--- TEST 1: CLOSED LEARNING LOOP ---")
    # Simulate a full analysis cycle
    bundle = await evidence_engine.collect_evidence()
    # Ensure it's pushed to core
    snapshot_id = bundle.snapshot_id
    
    from backend.core.ai_host.planner.task_planner import TaskPlan, PlanType
    plan = TaskPlan(goal="Stabilization Test Plan", plan_type=PlanType.DIAGNOSTIC)
    plan.add_step("read", "Checking state")
    
    print("Running process_analysis...")
    res = await brain_router._process_analysis("Omni, analyze systems", "en", None, plan, evidence_bundle=bundle)
    
    # Check outcomes in history
    last_record = adaptive_learning.learning_history[-1]
    print(f"Record created in AdaptiveLearning: {last_record.plan_id}")
    print(f"Outcome traced: {last_record.execution_outcome}")
    
    if last_record.hypothesis_id:
        h = cognitive_core.hypotheses.get(last_record.hypothesis_id)
        print(f"Hypothesis {h.description} status: {h.status}")
        print(f"Confidence after success: {h.confidence}")

    print("\n--- TEST 2: CONFIDENCE CHANGE QUERY ---")
    res_conf = await brain_router.process("Omni, ¿qué hipótesis aumentó su confianza?")
    print(f"Response:\n{res_conf.message}")

    print("\n--- TEST 3: LEARNING FROM FAILURE ---")
    # Manually trigger a failure record
    adaptive_learning.record_outcome(
        plan_id="failed-plan-01",
        hypothesis_id=list(cognitive_core.hypotheses.keys())[0],
        outcome="FAILED",
        evidence=["test.error=True"]
    )
    res_fail = await brain_router.process("Dime qué aprendiste del último diagnóstico fallido.")
    print(f"Response:\n{res_fail.message}")

    print("\n--- TEST 4: PATTERN DETECTION ---")
    res_pattern = await brain_router.process("¿Qué patrón estás detectando?")
    print(f"Response:\n{res_pattern.message}")

    print("\n--- TEST 5: EVIDENCE RELIABILITY ---")
    res_rel = await brain_router.process("muéstrame el reporte de confiabilidad de evidencia")
    print(f"Response:\n{res_rel.message}")

    print("\n--- TEST 6: INTENT SAFETY ---")
    # This sentence is a learning summary, not a chip command
    msg_safe = "He aprendido que latencias altas en ai_to_chips correlacionan con fallos de ejecución."
    print(f"Testing intent safety for: '{msg_safe}'")
    res_intent = await brain_router.process(msg_safe)
    
    # It should NOT be routed to ChipOrchestrator as 'ai_to_chips' (which is not a chip name)
    # Expected result: handled as chat/unknown or diagnostic fallback, NOT chip activation
    print(f"Intent returned: {res_intent.intent}")
    print(f"Response message start: {res_intent.message[:50]}...")

if __name__ == "__main__":
    try:
        asyncio.run(test_stage13_stabilization())
    except Exception as e:
        print(f"\nERROR DURING TEST: {e}")
        import traceback
        traceback.print_exc()
