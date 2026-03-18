import sys
import os

# Add project root to path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../.."))
sys.path.append(project_root)

from backend.core.ai_host.audit import cognitive_auditor

def run_tests():
    print("=== OMNIWEB COGNITIVE AUDIT LAYER V1 - RUNTIME VALIDATION ===\n")

    test_cases = [
        {
            "name": "Case 1: Valid Forced Choice A/B",
            "text": "He tomado una postura: elijo el chip_core. Descarto completamente la latencia porque el impacto estructural demanda tracción en el núcleo ahora mismo.",
            "intent": "COGNITIVE_COMMITMENT",
            "metadata": {"lang": "es"}
        },
        {
            "name": "Case 2: Evasive Forced Choice (Fails)",
            "text": "Lo tengo claro, pero depende de cómo lo miremos. Parece que hay algo raro en el flujo así que voy a mirar más.",
            "intent": "COGNITIVE_COMMITMENT",
            "metadata": {"lang": "es"}
        },
        {
            "name": "Case 3: Mixed Language Contamination (Fails)",
            "text": "The analysis indicates that the core system está estable pero sometimes it fails a bit ruidosamente.",
            "intent": "ANALYSIS_INTENT",
            "metadata": {"lang": "es"}
        },
        {
            "name": "Case 4: Technical Output with Narrative Residue (Fails)",
            "text": "DIAGNÓSTICO: Fallo en el búfer de entrada. ACCIÓN: Reiniciar módulo. \n\n Bueno, espero que eso te sirva, avisame si necesitas algo más che.",
            "intent": "COGNITIVE_DECOMPOSITION",
            "metadata": {"lang": "es"}
        }
    ]

    for case in test_cases:
        print(f"--- {case['name']} ---")
        print(f"Input: {case['text']}\n")
        
        result = cognitive_auditor.audit_response(
            response_text=case['text'],
            intent_group=case['intent'],
            metadata=case['metadata']
        )
        
        print(f"Passed: {result.passed}")
        print(f"Failures: {result.failure_types}")
        print(f"Severity: {result.severity}")
        print(f"Explanation: {result.explanation}")
        print(f"Rec Action: {result.recommended_action}")
        print(f"Rec Tool: {result.recommended_tool}")
        print("\n")

if __name__ == "__main__":
    run_tests()
