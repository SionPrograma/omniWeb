import asyncio
from backend.core.ai_host.reasoning.runtime_truth import runtime_truth, DiagnosisCategory
from backend.core.ai_host.reasoning.evidence_engine import EvidenceBundle, EvidenceItem
from backend.core.ai_host.planner.task_planner import task_planner, ActionableTask, ActionType
from backend.core.ai_host.reasoning.verification_layer import verification_layer
import json

def pprint_verif(scenario_name, v):
    print(f"\n[{scenario_name.upper()}]")
    print(f"Resultado Global: {'VALIDO' if v.is_overall_valid else 'INVALIDO'}")
    print(f"Modo Final      : {v.verification_mode}")
    if v.global_notes:
        print(f"Notas           : {v.global_notes}")
    for tv in v.task_verifications:
        print(f"  - Tarea {tv.task_id}: {tv.status} | Requerido Approval: {tv.requires_approval} | Motivo: {tv.reject_reason}")

def test_verification_logic():
    print("=== INICIANDO PRUEBAS DE VERIFICACIÓN LOCAL (ADUANA) ===")

    # 1. Caso Válido (Latencia -> Restart Bus)
    b1 = EvidenceBundle(items=[EvidenceItem("system", "flow.core.latency", 400)], has_sufficient_evidence=True)
    diag1 = runtime_truth.evaluate(b1)
    plan1 = task_planner.create_plan_from_diagnosis(diag1)
    v1 = verification_layer.verify(diag1, plan1)
    pprint_verif("Válido: Latencia", v1)

    # 2. Caso Contradictorio (Nominal pero plan tiene Restart)
    b2 = EvidenceBundle(items=[], has_sufficient_evidence=True) # Nominal logic
    diag2 = runtime_truth.evaluate(b2)
    # Forzamos un plan con reinicio de manual
    plan2 = task_planner.create_plan_from_diagnosis(diag2)
    plan2.tasks.append(ActionableTask(id=9, action_type=ActionType.RESTART, target_id="gateway_bus", is_dangerous=True, reason="Reinicio pirata"))
    v2 = verification_layer.verify(diag2, plan2)
    pprint_verif("Contradictorio: Nominal con Reinicio", v2)

    # 3. Target Inexistente (Plan a chip que no existe)
    b3 = EvidenceBundle(items=[EvidenceItem("system", "health", "warning")], has_sufficient_evidence=True)
    diag3 = runtime_truth.evaluate(b3)
    plan3 = task_planner.create_plan_from_diagnosis(diag3)
    # Inyectamos tarea a chip basura
    plan3.tasks.append(ActionableTask(id=77, action_type=ActionType.AUDIT, target_id="chip-fantasma", reason="Auditando la nada"))
    v3 = verification_layer.verify(diag3, plan3)
    pprint_verif("Inexistente: Chip Fantasma", v3)

    # 4. Inconsistencia Lógica (Memoria -> Reinicio de Bus)
    b4 = EvidenceBundle(items=[EvidenceItem("system", "os.memory", 98)], has_sufficient_evidence=True)
    diag4 = runtime_truth.evaluate(b4)
    plan4 = task_planner.create_plan_from_diagnosis(diag4)
    # Cambiamos el target del plan de memoria a un bus (no tiene sentido técnico)
    plan4.tasks[0].target_id = "gateway_bus"
    plan4.tasks[0].action_type = ActionType.RESTART
    v4 = verification_layer.verify(diag4, plan4)
    pprint_verif("Inconsistente: Memoria vs Bus", v4)

test_verification_logic()
