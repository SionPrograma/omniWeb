
import sys
import os

# Add the project root to sys.path
sys.path.append(r"c:\Users\Propietario\Desktop\plan actual\07-proyectosGrandes\01-omniweb")

from backend.core.ai_host.intent_understanding.human_input_interpreter import human_interpreter
from backend.core.ai_host.orchestration.mission_orchestrator import mission_orchestrator

test_cases = [
    "Optimiza la latencia del shell sin romper el auth",
    "Arreglá el dashboard móvil pero no toques el shell público",
    "Auditá el creator mode, y si afecta core frená y avisame"
]

print("--- MISSION TRANSLATION VALIDATION ---")
for text in test_cases:
    # 1. Interpret
    interpretation = human_interpreter.interpret(text)
    
    # 2. Plan
    mission_orchestrator.plan_mission(text, intent="copilot_proposal", interpretation=interpretation)
    
    # 3. Report
    report = mission_orchestrator.format_orchestration_report()
    
    print(f"\nINPUT: {text}")
    print(report)
    print("-" * 50)
