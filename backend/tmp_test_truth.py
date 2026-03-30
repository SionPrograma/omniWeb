import asyncio
from backend.core.ai_host.reasoning.runtime_truth import runtime_truth
from backend.core.ai_host.reasoning.evidence_engine import EvidenceBundle, EvidenceItem
import json

def pprint_diagnosis(scenario_name, d):
    print(f"\n[{scenario_name.upper()}]")
    print(f"Tipo de Diagnóstico : {d.diagnosis_type}")
    print(f"Puntaje de Confianza: {d.confidence_score}")
    print(f"Anomalías Físicas   : {json.dumps(d.detected_anomalies, indent=2)}")
    print(f"Necesita Aclaración : {d.clarification_needed}")
    print(f"Modo Sugerido       : {d.recommended_mode}")
    print(f"Legacy Claim (str)  : {d.claim}")

def test_scenarios():
    print("=== INICIANDO PRUEBAS DE ESTRUCTURACION MATEMÁTICA ===")

    # 1. Latencia Alta
    b1 = EvidenceBundle(items=[
        EvidenceItem("system_state", "health", "healthy"),
        EvidenceItem("system", "flow.core.latency", 450)
    ], has_sufficient_evidence=True)
    d1 = runtime_truth.evaluate(b1)
    pprint_diagnosis("Latencia Alta", d1)

    # 2. Memoria Saturada
    b2 = EvidenceBundle(items=[
        EvidenceItem("system_state", "health", "healthy"),
        EvidenceItem("system", "os.memory", 92)
    ], has_sufficient_evidence=True)
    d2 = runtime_truth.evaluate(b2)
    pprint_diagnosis("Memoria Saturada", d2)

    # 3. Conflicto (User dice bug pero salud = perfect)
    b3 = EvidenceBundle(items=[
        EvidenceItem("system_state", "health", "healthy"),
        EvidenceItem("system", "os.memory", 45)
    ], has_sufficient_evidence=True)
    d3 = runtime_truth.evaluate(b3, request_msg="hey omni el chip está roto banda")
    pprint_diagnosis("Conflicto Sentimiento/Métrica", d3)

    # 4. Inconsistencia Interna (Warning pero sin data rota)
    b4 = EvidenceBundle(items=[
        EvidenceItem("system_state", "health", "warning")
    ], has_sufficient_evidence=True)
    d4 = runtime_truth.evaluate(b4)
    pprint_diagnosis("Warning Fantasma", d4)

    # 5. Fallo Genérico de Chip
    b5 = EvidenceBundle(items=[
        EvidenceItem("system_state", "health", "warning"),
        EvidenceItem("chip_finanzas", "status", "ERROR_FAILED_BOOT")
    ], has_sufficient_evidence=True)
    d5 = runtime_truth.evaluate(b5)
    pprint_diagnosis("Fallo Específico de Modulo", d5)

test_scenarios()
