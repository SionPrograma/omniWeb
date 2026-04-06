
import sys
import re
from typing import Dict, Any, List

# REPRODUCING THE LOGIC FROM human_input_interpreter.py to validate extraction
class HumanInputInterpreterMock:
    def _extract_structured_mission(self, msg: str) -> Dict[str, Any]:
        surfaces = {
            "shell": ["shell", "ui", "interfaz", "interfaz pública", "shell público"],
            "auth": ["auth", "login", "seguridad", "permisos", "sesión", "session"],
            "dashboard": ["dashboard", "pizarrón", "pizarron", "misiones", "cockpit"],
            "core": ["núcleo", "core", "backend", "procesamiento", "lógica interna"],
            "mobile": ["móvil", "celular", "mobile", "ios", "android"],
            "creator": ["creator mode", "creador", "workspace", "workspace del creador"]
        }
        detected_surfaces = []
        for s, keywords in surfaces.items():
            if any(k in msg.lower() for k in keywords):
                detected_surfaces.append(s)
        constraints = []
        stop_conditions = []
        c_matches = re.findall(r"(?:sin|pero no|no toques|no rompas|no afectes|sin afectar)\s+([^,.]+)", msg.lower())
        for sub in c_matches:
            constraints.append(sub.strip())
        s_matches = re.findall(r"si\s+([^,.]+)\s+(?:frená|avisame|pará|parar|escalar)", msg.lower())
        for sub in s_matches:
            stop_conditions.append(sub.strip())
        execution_style = "standard"
        if any(w in msg.lower() for w in ["auditá", "audita", "revisá", "inspeccioná", "audit_only"]):
            execution_style = "audit_first"
        if any(w in msg.lower() for w in ["patch mínimo", "mínimo impacto", "no rompas nada", "con cuidado"]):
            execution_style = "surgical_patch"
        if any(w in msg.lower() for w in ["avisame", "frená", "confirmar", "preguntame"]):
             execution_style += "_with_confirmation"
        risk = "low"
        sensitive_layers = ["auth", "core", "seguridad", "permisos"]
        if any(s in detected_surfaces for s in ["auth", "core"]):
            risk = "high"
        elif constraints:
            risk = "medium"
        objective = msg.lower()
        intro_verbs = [r"^optimizá\s+", r"^optimiza\s+", r"^arreglá\s+", r"^arregla\s+", r"^auditá\s+", r"^audita\s+", r"^creá\s+", r"^crea\s+"]
        for verb in intro_verbs:
            objective = re.sub(verb, "", objective)
        objective = re.split(r"(?:sin|pero no|no toques|no rompas|no afectes|si afecta)", objective)[0].strip()
        return {
            "objective": objective,
            "surface_affected": detected_surfaces,
            "constraints": constraints,
            "stop_conditions": stop_conditions,
            "risk_level": risk,
            "execution_style": execution_style,
            "expected_outcome": "Misión técnica estabilizada" if risk != "high" else "Actualización segura del núcleo",
            "sensitive_layers_detected": [s for s in detected_surfaces if s in sensitive_layers]
        }

interpreter = HumanInputInterpreterMock()
test_cases = [
    "Optimiza la latencia del shell sin romper el auth",
    "Arreglá el dashboard móvil pero no toques el shell público",
    "Auditá el creator mode, y si afecta core o seguridad frená y avisame"
]

print("--- DEEP INTAKE VALIDATION (Isolated Logic) ---")
for text in test_cases:
    structured = interpreter._extract_structured_mission(text)
    print(f"\nINPUT: {text}")
    print(f"  > OBJECTIVE: {structured['objective']}")
    print(f"  > SURFACE: {structured['surface_affected']}")
    print(f"  > CONSTRAINTS: {structured['constraints']}")
    print(f"  > STOP CONDITIONS: {structured['stop_conditions']}")
    print(f"  > RISK LEVEL: {structured['risk_level']}")
    print(f"  > STYLE: {structured['execution_style']}")
    print(f"  > SENSITIVE LAYERS: {structured['sensitive_layers_detected']}")
