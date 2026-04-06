
import sys
import os

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")


from backend.core.ai_host.intent_understanding.human_input_interpreter import human_interpreter


test_cases = [
    "Optimiza la latencia del shell sin romper el auth",
    "Arreglá el dashboard móvil pero no toques el shell público",
    "Auditá el creator mode, y si afecta core o seguridad frená y avisame"
]

print("--- DEEP INTAKE VALIDATION ---")
for text in test_cases:
    res = human_interpreter.interpret(text)
    structured = res.get("structured_mission")
    print(f"\nINPUT: {text}")
    print(f"OBJECTIVE: {structured['objective']}")
    print(f"SURFACE: {structured['surface_affected']}")
    print(f"CONSTRAINTS: {structured['constraints']}")
    print(f"STOP CONDITIONS: {structured['stop_conditions']}")
    print(f"RISK LEVEL: {structured['risk_level']}")
    print(f"STYLE: {structured['execution_style']}")
    print(f"SENSITIVE LAYERS: {structured['sensitive_layers_detected']}")
