
import sys
import os
import json

# REPRODUCING THE TACTICAL OVERLAY CONSTRUCTION FOR VALIDATION
def construct_tactical_overlay(mission, phases):
    tactical_overlay = {
        "branding": "OmniWeb Core",
        "understood_intent": mission.get("objective"),
        "mission_summary": f"Operación técnica sobre {', '.join(mission.get('surface_affected', []))}",
        "affected_surface": mission.get("surface_affected"),
        "constraints": mission.get("constraints"),
        "risk_state": mission.get("risk_level"),
        "governance_state": "AUDIT_LOCK_ACTIVE" if mission.get("risk_level") == "high" else "NOMINAL",
        "execution_path": phases,
        "next_action": "Esperando validación de Preview" if "with_confirmation" in mission.get("execution_style", "") else "Proveer feedback sobre el plan sugerido"
    }
    return tactical_overlay

# Mocked structured missions from Step 1
test_cases = [
    {
        "text": "Optimiza la latencia del shell sin romper el auth",
        "mission": {
            "objective": "la latencia del shell",
            "surface_affected": ["shell", "auth"],
            "constraints": ["romper el auth"],
            "risk_level": "high",
            "execution_style": "standard"
        },
        "phases": [
            {"name": "OBJETIVO_ESTABLECIDO", "status": "COMPLETADO", "detail": "Intención: la latencia del shell"},
            {"name": "FOCO_TÉCNICO", "status": "COMPLETADO", "detail": "Superficie: [shell, auth]"},
            {"name": "LÍMITES_OPERATIVOS", "status": "COMPLETADO", "detail": "Restricciones: romper el auth"},
            {"name": "COGNITIVE_GOVERNANCE_LOCK", "status": "BLOQUEADO", "detail": "RIESGO ALTO..."}
        ]
    },
    {
        "text": "Arreglá el dashboard móvil pero no toques el shell público",
        "mission": {
            "objective": "el dashboard móvil",
            "surface_affected": ["shell", "dashboard", "mobile"],
            "constraints": ["toques el shell público"],
            "risk_level": "medium",
            "execution_style": "standard"
        },
        "phases": [
            {"name": "OBJETIVO_ESTABLECIDO", "status": "COMPLETADO", "detail": "Intención: el dashboard móvil"},
            {"name": "EVALUACIÓN_RIESGO", "status": "COMPLETADO", "detail": "Nivel: MEDIUM"}
        ]
    },
    {
        "text": "Auditá el creator mode, y si afecta core frená y avisame",
        "mission": {
            "objective": "el creator mode",
            "surface_affected": ["auth", "core", "creator"],
            "constraints": [],
            "risk_level": "high",
            "execution_style": "audit_first_with_confirmation"
        },
        "phases": [
            {"name": "OBJETIVO_ESTABLECIDO", "status": "COMPLETADO", "detail": "Intención: el creator mode"},
            {"name": "AUDITORÍA_PREVIA", "status": "PROCESANDO", "detail": "Modo Inspección Activo..."}
        ]
    }
]

print("--- EXPRESSION LAYER VALIDATION ---")
for case in test_cases:
    overlay = construct_tactical_overlay(case["mission"], case["phases"])
    print(f"\nINPUT: {case['text']}")
    print(f"TACTICAL_OVERLAY_JSON: {json.dumps(overlay, indent=2)}")
    print("-" * 50)
