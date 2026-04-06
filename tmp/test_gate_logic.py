import re
from typing import Dict, Any

# Mock settings
class MockSettings:
    CREATOR_PIN = "1234"

settings = MockSettings()

def evaluate_mission_gate(mission_data: Dict[str, Any], authority_info: Dict[str, Any]) -> Dict[str, Any]:
    risk = (mission_data.get("risk_level") or "low").lower()
    surface = set(mission_data.get("surface_affected") or [])
    
    critical_surfaces = {"core", "auth", "security", "infra", "governance"}
    is_constitutional_sensitive = any(s in surface for s in critical_surfaces)
    
    gate = {
        "required": False,
        "level": "NORMAL",
        "type": "CONFIRM",
        "reason": ""
    }

    if risk == "critical" or is_constitutional_sensitive:
        gate["required"] = True
        gate["level"] = "CRITICAL"
        gate["type"] = "PIN"
        gate["reason"] = f"INTEGRIDAD CRÍTICA: ... {', '.join(surface)}"
    elif risk == "high":
        gate["required"] = True
        gate["level"] = "HIGH"
        gate["type"] = "REINFORCED"
        gate["reason"] = f"RIESGO ELEVADO: ... {', '.join(surface)}"
    
    if authority_info.get("active"):
        gate["required"] = False
        
    return gate

# Test Case 1: Low Risk
m1 = {"risk_level": "low", "surface_affected": ["ui"]}
print(f"Test 1 (Low): {evaluate_mission_gate(m1, {'active': False})}")

# Test Case 2: Critical Core
m2 = {"risk_level": "medium", "surface_affected": ["core", "ui"]}
print(f"Test 2 (Critical Core): {evaluate_mission_gate(m2, {'active': False})}")

# Test Case 3: High Risk
m3 = {"risk_level": "high", "surface_affected": ["logic"]}
print(f"Test 3 (High): {evaluate_mission_gate(m3, {'active': False})}")

# Simulation of Orchestrate Logic
def simulate_orchestrate(message, mission, auth_active=False):
    authority_info = {"active": auth_active}
    gate = evaluate_mission_gate(mission, authority_info)
    
    provided_pin = None
    pin_match = re.search(r"--pin=([\w]+)", message, re.IGNORECASE)
    if pin_match: provided_pin = pin_match.group(1)
    
    force_intake = False
    gate_error = None
    
    if "--confirmed=true" in message.lower() and gate["required"]:
        if gate["type"] == "PIN":
            if provided_pin == settings.CREATOR_PIN:
                gate["required"] = False
            else:
                force_intake = True
                gate_error = "PIN_INVALID"
    
    is_intake = "--confirmed=true" not in message or force_intake
    
    return {"is_intake": is_intake, "gate": gate, "error": gate_error}

print(f"Sim 1 (Confirm critical NO PIN): {simulate_orchestrate('--confirmed=true', m2)}")
print(f"Sim 2 (Confirm critical WRONG PIN): {simulate_orchestrate('--confirmed=true --pin=9999', m2)}")
print(f"Sim 3 (Confirm critical VALID PIN): {simulate_orchestrate('--confirmed=true --pin=1234', m2)}")
