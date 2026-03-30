import asyncio
from backend.core.ai_host.reasoning.runtime_truth import runtime_truth
from backend.core.ai_host.reasoning.evidence_engine import EvidenceBundle, EvidenceItem
from backend.core.ai_host.planner.task_planner import task_planner
from backend.core.ai_host.reasoning.verification_layer import verification_layer
from backend.core.ai_host.orchestration.executive_synthesis import executive_synthesis
import json

def test_synthesis_flow():
    print("=== INICIANDO PRUEBAS DE SÍNTESIS TÉCNICA ESTRUCTURADA ===")

    # 1. Caso: Latencia con Aprobación Pendiente
    b1 = EvidenceBundle(items=[EvidenceItem("system", "flow.core.latency", 400)], has_sufficient_evidence=True)
    diag1 = runtime_truth.evaluate(b1)
    plan1 = task_planner.create_plan_from_diagnosis(diag1)
    v1 = verification_layer.verify(diag1, plan1)
    # Simulamos estado de ejecución en "WAITING_CONFIRMATION" en el paso 2
    exec_res1 = {"status": "WAITING_CONFIRMATION", "steps_completed": [1], "current_step": 2}
    
    res1 = executive_synthesis.synthesize_analysis(diag1, plan1, v1, exec_res1, chip_report="core: active\nfinanzas: active")
    print("\n[ESCENARIO 1: LATENCIA + APPROVAL]")
    print(res1)

    # 2. Caso: Bloqueo por Target Inexistente
    b2 = EvidenceBundle(items=[EvidenceItem("system", "health", "warning")], has_sufficient_evidence=True)
    diag2 = runtime_truth.evaluate(b2)
    plan2 = task_planner.create_plan_from_diagnosis(diag2)
    from backend.core.ai_host.planner.task_planner import ActionableTask, ActionType
    plan2.tasks.append(ActionableTask(id=99, action_type=ActionType.PATCH, target_id="chip-fantasma", reason="Parcheando aire"))
    v2 = verification_layer.verify(diag2, plan2)
    exec_res2 = {"status": "BLOCKED", "steps_completed": [], "current_step": 0}
    
    res2 = executive_synthesis.synthesize_analysis(diag2, plan2, v2, exec_res2)
    print("\n[ESCENARIO 2: BLOQUEADO]")
    print(res2)

    # 3. Caso: Nominal con Pedido Ambiguo
    b3 = EvidenceBundle(items=[], has_sufficient_evidence=True)
    diag3 = runtime_truth.evaluate(b3, request_msg="hey algo anda mal")
    plan3 = task_planner.create_plan_from_diagnosis(diag3)
    v3 = verification_layer.verify(diag3, plan3)
    exec_res3 = {"status": "RUNNING", "steps_completed": [], "current_step": 1}
    
    res3 = executive_synthesis.synthesize_analysis(diag3, plan3, v3, exec_res3)
    print("\n[ESCENARIO 3: NOMINAL + AMBIGUO]")
    print(res3)

test_synthesis_flow()
