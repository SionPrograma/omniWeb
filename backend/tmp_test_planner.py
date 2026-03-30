import asyncio
from backend.core.ai_host.reasoning.runtime_truth import runtime_truth, DiagnosisCategory
from backend.core.ai_host.reasoning.evidence_engine import EvidenceBundle, EvidenceItem
from backend.core.ai_host.planner.task_planner import task_planner
import json

def pprint_plan(scenario_name, plan):
    print(f"\n[{scenario_name.upper()}]")
    print(f"Meta del Plan: {plan.goal}")
    print(f"Tareas Operativas:")
    for t in plan.tasks:
        print(f"  - [{t.action_type}] en {t.target_id}: {t.reason} (Dangerous: {t.is_dangerous})")
    print(f"Modo ejecución: {plan.execution_mode}")

def test_planner_logic():
    print("=== INICIANDO PRUEBAS DE PLANIFICACIÓN OPERATIVA ===")

    # 1. Escenario Latencia
    b1 = EvidenceBundle(items=[EvidenceItem("system", "flow.core.latency", 400)], has_sufficient_evidence=True)
    diag1 = runtime_truth.evaluate(b1)
    plan1 = task_planner.create_plan_from_diagnosis(diag1)
    pprint_plan("Spike de Latencia", plan1)

    # 2. Escenario Memoria
    b2 = EvidenceBundle(items=[EvidenceItem("system", "os.memory", 95)], has_sufficient_evidence=True)
    diag2 = runtime_truth.evaluate(b2)
    plan2 = task_planner.create_plan_from_diagnosis(diag2)
    pprint_plan("Saturación RAM", plan2)

    # 3. Escenario Chip Error
    b3 = EvidenceBundle(items=[
        EvidenceItem("chip_finanzas", "status", "ERROR_FAILED")
    ], has_sufficient_evidence=True)
    diag3 = runtime_truth.evaluate(b3)
    plan3 = task_planner.create_plan_from_diagnosis(diag3)
    pprint_plan("Error en Chip Finanzas", plan3)

    # 4. Escenario Ambiguo
    b4 = EvidenceBundle(items=[], has_sufficient_evidence=False)
    diag4 = runtime_truth.evaluate(b4, request_msg="no anda nada")
    plan4 = task_planner.create_plan_from_diagnosis(diag4)
    pprint_plan("Petición Ambigua", plan4)

test_planner_logic()
